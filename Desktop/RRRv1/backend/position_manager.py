"""
Position Management and Reconciliation for RRRv1 Trading System

Handles:
- Position persistence to database
- Position recovery on startup
- Exchange reconciliation
- Position lifecycle tracking
- Risk calculations
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json

from database import TradingDatabase

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Position lifecycle states"""
    OPENING = "opening"           # Trade initiated, waiting for confirmation
    OPEN = "open"                 # Position established and active
    CLOSING = "closing"           # Close order submitted
    CLOSED = "closed"             # Position fully closed
    LIQUIDATED = "liquidated"     # Position liquidated due to margin call
    REDUCED = "reduced"           # Position partially reduced


class ReconciliationStatus(Enum):
    """Reconciliation result states"""
    SYNCED = "synced"             # Position matches exchange
    DRIFT_DETECTED = "drift"      # Position differs from exchange
    SYNC_FAILED = "failed"        # Could not reconcile
    PENDING_SYNC = "pending"      # Awaiting next sync attempt


@dataclass
class Position:
    """Represents a single trading position"""
    asset: str
    entry_price: float
    current_price: float
    size: float
    leverage: float
    venue: str
    status: PositionStatus = PositionStatus.OPEN
    liquidation_price: Optional[float] = None
    opened_at: Optional[str] = None
    closed_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_reconciled_at: Optional[str] = None
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING_SYNC
    exchange_position_id: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit_targets: Optional[List[float]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary, handling enums"""
        data = asdict(self)
        data['status'] = self.status.value
        data['reconciliation_status'] = self.reconciliation_status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """Create Position from dictionary, handling enum conversion"""
        # Convert string enums back to enum
        data_copy = data.copy()
        if isinstance(data_copy.get('status'), str):
            data_copy['status'] = PositionStatus(data_copy['status'])
        if isinstance(data_copy.get('reconciliation_status'), str):
            data_copy['reconciliation_status'] = ReconciliationStatus(data_copy['reconciliation_status'])

        return cls(**data_copy)

    def calculate_pnl(self) -> float:
        """Calculate unrealized P&L"""
        return (self.current_price - self.entry_price) * self.size

    def calculate_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.entry_price == 0:
            return 0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100

    def calculate_liquidation_distance(self) -> float:
        """Calculate distance to liquidation price as percentage"""
        if not self.liquidation_price or self.current_price == 0:
            return 999.0
        return ((self.current_price - self.liquidation_price) / self.current_price) * 100

    def is_liquidation_risk(self, threshold_pct: float = 5.0) -> bool:
        """Check if position is near liquidation"""
        return self.calculate_liquidation_distance() < threshold_pct

    def get_margin_ratio(self) -> float:
        """Calculate current margin ratio"""
        if not self.liquidation_price or self.current_price == 0:
            return 0
        return (self.current_price - self.liquidation_price) / self.current_price


class PositionManager:
    """
    Manages position persistence, recovery, and reconciliation.

    Provides:
    - Save/load positions from database
    - Automatic recovery on startup
    - Exchange reconciliation
    - Position lifecycle tracking
    - Risk monitoring
    """

    def __init__(self, database: Optional[TradingDatabase] = None):
        """
        Initialize position manager.

        Args:
            database: TradingDatabase instance
        """
        self.db = database or TradingDatabase()
        self.positions: Dict[str, Position] = {}
        self._load_positions_from_db()

    def _load_positions_from_db(self) -> None:
        """Load all open positions from database on startup"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM positions
                WHERE status NOT IN ('closed', 'liquidated')
                ORDER BY opened_at DESC
            """)

            for row in cursor.fetchall():
                pos_data = dict(row)
                position = Position.from_dict(pos_data)
                self.positions[position.asset] = position
                logger.info(f"Recovered position: {position.asset} (size: {position.size})")

            logger.info(f"Recovered {len(self.positions)} open positions from database")
        except Exception as e:
            logger.error(f"Failed to load positions from database: {e}")

    def add_position(self, position: Position) -> None:
        """
        Add or update position and persist to database.

        Args:
            position: Position object to add
        """
        try:
            # Update in-memory positions
            self.positions[position.asset] = position

            # Persist to database
            if not position.opened_at:
                position.opened_at = datetime.utcnow().isoformat()
            position.updated_at = datetime.utcnow().isoformat()

            with self.db._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO positions
                    (asset, entry_price, current_price, size, leverage, venue,
                     status, liquidation_price, opened_at, updated_at, last_reconciled_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position.asset,
                    position.entry_price,
                    position.current_price,
                    position.size,
                    position.leverage,
                    position.venue,
                    position.status.value,
                    position.liquidation_price,
                    position.opened_at,
                    position.updated_at,
                    position.last_reconciled_at
                ))

                # Record in position history
                cursor.execute("""
                    INSERT INTO position_history (asset, event_type, new_values, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    position.asset,
                    'opened' if not position.last_reconciled_at else 'updated',
                    json.dumps(position.to_dict()),
                    datetime.utcnow().isoformat()
                ))

            logger.info(f"Position persisted: {position.asset} (size: {position.size})")
        except Exception as e:
            logger.error(f"Failed to add position {position.asset}: {e}")
            raise

    def close_position(self, asset: str, close_price: float) -> Optional[Position]:
        """
        Close a position and record in database.

        Args:
            asset: Asset identifier
            close_price: Price at which position was closed

        Returns:
            Closed position or None if not found
        """
        try:
            position = self.positions.get(asset)
            if not position:
                logger.warning(f"Attempted to close non-existent position: {asset}")
                return None

            # Calculate realized P&L
            realized_pnl = (close_price - position.entry_price) * position.size

            # Update position
            position.current_price = close_price
            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.utcnow().isoformat()
            position.updated_at = position.closed_at

            # Persist closure
            with self.db._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE positions
                    SET status = ?, current_price = ?, closed_at = ?, updated_at = ?
                    WHERE asset = ?
                """, (
                    position.status.value,
                    close_price,
                    position.closed_at,
                    position.updated_at,
                    asset
                ))

                # Record position closure in history
                cursor.execute("""
                    INSERT INTO position_history (asset, event_type, new_values, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    asset,
                    'closed',
                    json.dumps({
                        'close_price': close_price,
                        'realized_pnl': realized_pnl,
                        'status': position.status.value
                    }),
                    position.closed_at
                ))

            # Remove from active positions
            del self.positions[asset]

            logger.info(f"Position closed: {asset} (P&L: {realized_pnl:.2f})")
            return position
        except Exception as e:
            logger.error(f"Failed to close position {asset}: {e}")
            raise

    def reduce_position(self, asset: str, reduction_size: float, reduction_price: float) -> Optional[Position]:
        """
        Reduce position size and record in database.

        Args:
            asset: Asset identifier
            reduction_size: Amount to reduce position by
            reduction_price: Price at which reduction occurred

        Returns:
            Updated position or None if not found
        """
        try:
            position = self.positions.get(asset)
            if not position:
                logger.warning(f"Attempted to reduce non-existent position: {asset}")
                return None

            if reduction_size > position.size:
                logger.warning(f"Reduction size {reduction_size} exceeds position size {position.size}")
                reduction_size = position.size

            # Calculate partial P&L
            partial_pnl = (reduction_price - position.entry_price) * reduction_size

            # Update position
            old_size = position.size
            position.size -= reduction_size
            position.current_price = reduction_price
            position.updated_at = datetime.utcnow().isoformat()

            if position.size <= 0:
                position.status = PositionStatus.CLOSED
                position.closed_at = position.updated_at
            else:
                position.status = PositionStatus.REDUCED

            # Persist reduction
            with self.db._transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE positions
                    SET size = ?, current_price = ?, status = ?, updated_at = ?
                    WHERE asset = ?
                """, (
                    position.size,
                    reduction_price,
                    position.status.value,
                    position.updated_at,
                    asset
                ))

                # Record reduction in history
                cursor.execute("""
                    INSERT INTO position_history (asset, event_type, new_values, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    asset,
                    'reduced',
                    json.dumps({
                        'old_size': old_size,
                        'new_size': position.size,
                        'reduced_amount': reduction_size,
                        'partial_pnl': partial_pnl,
                        'reduction_price': reduction_price
                    }),
                    position.updated_at
                ))

            logger.info(f"Position reduced: {asset} (from {old_size} to {position.size})")
            return position
        except Exception as e:
            logger.error(f"Failed to reduce position {asset}: {e}")
            raise

    def update_position_prices(self, price_updates: Dict[str, float]) -> None:
        """
        Update current prices for multiple positions.

        Args:
            price_updates: Dictionary of {asset: price}
        """
        try:
            for asset, price in price_updates.items():
                if asset in self.positions:
                    position = self.positions[asset]
                    position.current_price = price
                    position.updated_at = datetime.utcnow().isoformat()

                    # Persist price update
                    with self.db._transaction() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE positions
                            SET current_price = ?, updated_at = ?
                            WHERE asset = ?
                        """, (price, position.updated_at, asset))

            logger.debug(f"Updated prices for {len(price_updates)} positions")
        except Exception as e:
            logger.error(f"Failed to update position prices: {e}")

    def get_position(self, asset: str) -> Optional[Position]:
        """Get position by asset"""
        return self.positions.get(asset)

    def get_all_positions(self) -> List[Position]:
        """Get all active positions"""
        return list(self.positions.values())

    def get_positions_by_status(self, status: PositionStatus) -> List[Position]:
        """Get positions filtered by status"""
        return [p for p in self.positions.values() if p.status == status]

    def get_positions_at_risk(self, threshold_pct: float = 5.0) -> List[Position]:
        """Get positions near liquidation"""
        return [p for p in self.positions.values() if p.is_liquidation_risk(threshold_pct)]

    def reconcile_with_exchange(self, exchange_positions: Dict[str, Dict]) -> Tuple[List[str], List[str], List[str]]:
        """
        Reconcile local positions with exchange data.

        Args:
            exchange_positions: Dictionary of positions from exchange {asset: position_data}

        Returns:
            Tuple of (synced_assets, drift_detected, missing_locally)
        """
        synced = []
        drifts = []
        missing = []

        try:
            # Check for drifts in existing positions
            for asset, local_pos in self.positions.items():
                if asset not in exchange_positions:
                    logger.warning(f"Position {asset} not found on exchange - potential issue")
                    drifts.append(asset)
                    local_pos.reconciliation_status = ReconciliationStatus.DRIFT_DETECTED
                    continue

                exchange_pos = exchange_positions[asset]

                # Compare critical fields
                size_match = abs(local_pos.size - exchange_pos.get('size', 0)) < 0.0001
                price_match = abs(local_pos.current_price - exchange_pos.get('current_price', 0)) < 0.01

                if size_match and price_match:
                    synced.append(asset)
                    local_pos.reconciliation_status = ReconciliationStatus.SYNCED
                    local_pos.last_reconciled_at = datetime.utcnow().isoformat()
                else:
                    drifts.append(asset)
                    local_pos.reconciliation_status = ReconciliationStatus.DRIFT_DETECTED
                    logger.warning(f"Drift detected for {asset}: local_size={local_pos.size} "
                                 f"exchange_size={exchange_pos.get('size', 0)}")

                # Update exchange position ID if available
                if 'position_id' in exchange_pos:
                    local_pos.exchange_position_id = exchange_pos['position_id']

            # Check for positions on exchange not in local state
            for asset in exchange_positions.keys():
                if asset not in self.positions:
                    missing.append(asset)
                    logger.warning(f"Position {asset} found on exchange but missing locally")

            logger.info(f"Reconciliation complete: {len(synced)} synced, {len(drifts)} drifts, {len(missing)} missing")
            return synced, drifts, missing

        except Exception as e:
            logger.error(f"Failed to reconcile with exchange: {e}")
            raise

    def get_portfolio_summary(self) -> Dict:
        """Get summary of all positions"""
        total_pnl = 0
        total_notional = 0
        at_risk_count = 0

        for position in self.positions.values():
            total_pnl += position.calculate_pnl()
            total_notional += position.entry_price * position.size * position.leverage

            if position.is_liquidation_risk():
                at_risk_count += 1

        return {
            'total_positions': len(self.positions),
            'total_unrealized_pnl': total_pnl,
            'total_notional_value': total_notional,
            'positions_at_risk': at_risk_count,
            'assets': list(self.positions.keys())
        }

    def get_position_history(self, asset: str, limit: int = 50) -> List[Dict]:
        """Get history of changes for a position"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM position_history
                WHERE asset = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (asset, limit))

            history = [dict(row) for row in cursor.fetchall()]
            return history
        except Exception as e:
            logger.error(f"Failed to get position history: {e}")
            return []

    def clear_closed_positions(self, older_than_days: int = 30) -> int:
        """
        Archive and clear closed positions older than specified days.

        Args:
            older_than_days: Only clear positions closed more than this many days ago

        Returns:
            Number of positions cleared
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()

            with self.db._transaction() as conn:
                cursor = conn.cursor()

                # Get count of positions to be cleared
                cursor.execute("""
                    SELECT COUNT(*) FROM positions
                    WHERE status = 'closed' AND closed_at < ?
                """, (cutoff_date,))

                count = cursor.fetchone()[0]

                # Delete old closed positions
                cursor.execute("""
                    DELETE FROM positions
                    WHERE status = 'closed' AND closed_at < ?
                """, (cutoff_date,))

                logger.info(f"Cleared {count} closed positions older than {older_than_days} days")
                return count
        except Exception as e:
            logger.error(f"Failed to clear closed positions: {e}")
            return 0
