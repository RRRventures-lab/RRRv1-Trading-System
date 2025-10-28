"""
Unified Exchange Integration Layer

Provides a unified interface for:
- Multi-exchange order placement
- Position management across venues
- Price feeds from exchanges
- Account balance tracking
- Allocation management (80% Hyperliquid, 20% Coinbase)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from hyperliquid_api import (
    HyperliquidAPIClient, HyperliquidPosition, HyperliquidOrder,
    OrderType as HLOrderType, OrderSide, OrderStatus
)
from coinbase_api import (
    CoinbaseAPIClient, CoinbasePosition, CoinbaseOrder,
    OrderType as CBOrderType, OrderSide as CBOrderSide
)
from position_manager import PositionManager, Position, PositionStatus

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    """Supported exchanges"""
    HYPERLIQUID = "hyperliquid"
    COINBASE = "coinbase"


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    success: bool
    exchange: ExchangeType
    asset: str
    order_id: str
    size: float
    price: Optional[float]
    status: str
    message: str
    timestamp: str


class UnifiedExchangeClient:
    """
    Unified interface for multiple exchanges.

    Manages:
    - Order execution across venues
    - Position tracking on both exchanges
    - Allocation enforcement (80/20 split)
    - Price feeds
    - Account management
    """

    def __init__(self,
                 hl_key: str,
                 hl_secret: str,
                 cb_key: str,
                 cb_secret: str,
                 position_manager: Optional[PositionManager] = None,
                 hl_testnet: bool = False):
        """
        Initialize unified exchange client.

        Args:
            hl_key: Hyperliquid API key
            hl_secret: Hyperliquid API secret
            cb_key: Coinbase API key
            cb_secret: Coinbase API secret
            position_manager: PositionManager instance
            hl_testnet: Use Hyperliquid testnet
        """
        self.hl_client = HyperliquidAPIClient(hl_key, hl_secret, testnet=hl_testnet)
        self.cb_client = CoinbaseAPIClient(cb_key, cb_secret)
        self.position_manager = position_manager or PositionManager()

        # Allocation targets
        self.hl_allocation = 0.80  # 80% Hyperliquid
        self.cb_allocation = 0.20  # 20% Coinbase

        # Session management
        self._session = None
        logger.info("Unified exchange client initialized")

    async def connect(self) -> None:
        """Connect to both exchanges"""
        try:
            await self.hl_client.connect()
            await self.cb_client.connect()
            logger.info("Connected to all exchanges")
        except Exception as e:
            logger.error(f"Failed to connect to exchanges: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from both exchanges"""
        try:
            await self.hl_client.disconnect()
            await self.cb_client.disconnect()
            logger.info("Disconnected from all exchanges")
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")

    # ========================================================================
    # Health & Status
    # ========================================================================

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of both exchanges.

        Returns:
            Dictionary with exchange health status
        """
        try:
            hl_health = await self.hl_client.health_check()
            cb_health = await self.cb_client.health_check()

            status = {
                "hyperliquid": hl_health,
                "coinbase": cb_health,
                "all_operational": hl_health and cb_health
            }

            logger.info(f"Health check: {status}")
            return status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Account Information
    # ========================================================================

    async def get_balances(self) -> Dict[str, Dict]:
        """
        Get balances from both exchanges.

        Returns:
            Dictionary with balance info from each exchange
        """
        try:
            hl_balance = await self.hl_client.get_balance()
            cb_balance = await self.cb_client.get_balance()

            total_balance = hl_balance.total_balance + cb_balance.total_balance

            return {
                "hyperliquid": hl_balance.__dict__,
                "coinbase": cb_balance.__dict__,
                "total": {
                    "total_balance": total_balance,
                    "available": hl_balance.available_balance + cb_balance.available_balance,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            raise

    # ========================================================================
    # Position Management
    # ========================================================================

    async def get_all_positions(self) -> Dict[str, List]:
        """
        Get all positions from both exchanges.

        Returns:
            Dictionary with positions from each exchange
        """
        try:
            hl_positions = await self.hl_client.get_open_positions()
            cb_positions = await self.cb_client.get_open_positions()

            return {
                "hyperliquid": [p.__dict__ for p in hl_positions],
                "coinbase": [p.__dict__ for p in cb_positions],
                "total_count": len(hl_positions) + len(cb_positions),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    async def get_position(self, asset: str) -> Optional[Dict]:
        """
        Get position across both exchanges.

        Args:
            asset: Asset identifier

        Returns:
            Position data or None
        """
        try:
            # Try Hyperliquid first
            hl_pos = await self.hl_client.get_position(asset)
            if hl_pos:
                return {
                    "exchange": "hyperliquid",
                    "position": hl_pos.__dict__
                }

            # Then try Coinbase (need to convert asset format)
            cb_asset = f"{asset}-USD"
            cb_pos = await self.cb_client.get_position(cb_asset)
            if cb_pos:
                return {
                    "exchange": "coinbase",
                    "position": cb_pos.__dict__
                }

            return None
        except Exception as e:
            logger.error(f"Failed to get position for {asset}: {e}")
            return None

    # ========================================================================
    # Order Execution
    # ========================================================================

    async def place_order(self,
                         asset: str,
                         side: str,
                         size: float,
                         exchange: Optional[ExchangeType] = None,
                         price: Optional[float] = None,
                         leverage: float = 1.0) -> ExecutionResult:
        """
        Place order on specified exchange (or auto-select based on allocation).

        Args:
            asset: Asset to trade
            side: "BUY" or "SELL"
            size: Order size
            exchange: Target exchange (auto-select if None)
            price: Price for limit orders
            leverage: Leverage multiplier

        Returns:
            ExecutionResult
        """
        try:
            # Auto-select exchange if not specified
            if not exchange:
                exchange = await self._select_exchange_for_order(size)

            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL

            if exchange == ExchangeType.HYPERLIQUID:
                order = await self.hl_client.place_order(
                    asset=asset,
                    side=order_side,
                    size=size,
                    price=price,
                    leverage=leverage
                )

                result = ExecutionResult(
                    success=True,
                    exchange=ExchangeType.HYPERLIQUID,
                    asset=asset,
                    order_id=order.order_id,
                    size=size,
                    price=price,
                    status=order.status.value,
                    message=f"Order placed on Hyperliquid",
                    timestamp=datetime.utcnow().isoformat()
                )

            else:  # Coinbase
                cb_side = CBOrderSide.BUY if side.upper() == "BUY" else CBOrderSide.SELL
                cb_asset = f"{asset}-USD"

                order = await self.cb_client.place_order(
                    product_id=cb_asset,
                    side=cb_side,
                    order_type=CBOrderType.LIMIT if price else CBOrderType.MARKET,
                    size=size,
                    price=price
                )

                result = ExecutionResult(
                    success=True,
                    exchange=ExchangeType.COINBASE,
                    asset=asset,
                    order_id=order.order_id,
                    size=size,
                    price=price,
                    status=order.status.value,
                    message=f"Order placed on Coinbase",
                    timestamp=datetime.utcnow().isoformat()
                )

            logger.info(f"Order executed: {result.exchange.value} {side} {size} {asset}")
            return result

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return ExecutionResult(
                success=False,
                exchange=exchange or ExchangeType.HYPERLIQUID,
                asset=asset,
                order_id="",
                size=size,
                price=price,
                status="FAILED",
                message=str(e),
                timestamp=datetime.utcnow().isoformat()
            )

    async def close_position(self, asset: str) -> ExecutionResult:
        """
        Close position on the exchange where it exists.

        Args:
            asset: Asset to close

        Returns:
            ExecutionResult
        """
        try:
            pos = await self.get_position(asset)
            if not pos:
                return ExecutionResult(
                    success=False,
                    exchange=ExchangeType.HYPERLIQUID,
                    asset=asset,
                    order_id="",
                    size=0,
                    price=None,
                    status="NOT_FOUND",
                    message=f"No position found for {asset}",
                    timestamp=datetime.utcnow().isoformat()
                )

            exchange = ExchangeType[pos["exchange"].upper()]

            if exchange == ExchangeType.HYPERLIQUID:
                order = await self.hl_client.close_position(asset)
                if not order:
                    raise Exception("Failed to close position")

                result = ExecutionResult(
                    success=True,
                    exchange=ExchangeType.HYPERLIQUID,
                    asset=asset,
                    order_id=order.order_id,
                    size=order.size,
                    price=order.price,
                    status=order.status.value,
                    message="Position closed on Hyperliquid",
                    timestamp=datetime.utcnow().isoformat()
                )

            else:  # Coinbase
                cb_asset = f"{asset}-USD"
                order = await self.cb_client.close_position(cb_asset)
                if not order:
                    raise Exception("Failed to close position")

                result = ExecutionResult(
                    success=True,
                    exchange=ExchangeType.COINBASE,
                    asset=asset,
                    order_id=order.order_id,
                    size=order.size,
                    price=order.price,
                    status=order.status.value,
                    message="Position closed on Coinbase",
                    timestamp=datetime.utcnow().isoformat()
                )

            logger.info(f"Position closed: {asset} on {result.exchange.value}")
            return result

        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return ExecutionResult(
                success=False,
                exchange=ExchangeType.HYPERLIQUID,
                asset=asset,
                order_id="",
                size=0,
                price=None,
                status="FAILED",
                message=str(e),
                timestamp=datetime.utcnow().isoformat()
            )

    async def reduce_position(self,
                             asset: str,
                             reduction_amount: float) -> ExecutionResult:
        """
        Reduce position on the exchange where it exists.

        Args:
            asset: Asset to reduce
            reduction_amount: Amount to reduce by

        Returns:
            ExecutionResult
        """
        try:
            pos = await self.get_position(asset)
            if not pos:
                return ExecutionResult(
                    success=False,
                    exchange=ExchangeType.HYPERLIQUID,
                    asset=asset,
                    order_id="",
                    size=0,
                    price=None,
                    status="NOT_FOUND",
                    message=f"No position found for {asset}",
                    timestamp=datetime.utcnow().isoformat()
                )

            exchange = ExchangeType[pos["exchange"].upper()]

            if exchange == ExchangeType.HYPERLIQUID:
                order = await self.hl_client.reduce_position(asset, reduction_amount)
                if not order:
                    raise Exception("Failed to reduce position")

                result = ExecutionResult(
                    success=True,
                    exchange=ExchangeType.HYPERLIQUID,
                    asset=asset,
                    order_id=order.order_id,
                    size=reduction_amount,
                    price=order.price,
                    status=order.status.value,
                    message=f"Position reduced by {reduction_amount} on Hyperliquid",
                    timestamp=datetime.utcnow().isoformat()
                )

            else:  # Coinbase
                cb_asset = f"{asset}-USD"
                order = await self.cb_client.reduce_position(cb_asset, reduction_amount)
                if not order:
                    raise Exception("Failed to reduce position")

                result = ExecutionResult(
                    success=True,
                    exchange=ExchangeType.COINBASE,
                    asset=asset,
                    order_id=order.order_id,
                    size=reduction_amount,
                    price=order.price,
                    status=order.status.value,
                    message=f"Position reduced by {reduction_amount} on Coinbase",
                    timestamp=datetime.utcnow().isoformat()
                )

            logger.info(f"Position reduced: {asset} ({reduction_amount} units)")
            return result

        except Exception as e:
            logger.error(f"Failed to reduce position: {e}")
            return ExecutionResult(
                success=False,
                exchange=ExchangeType.HYPERLIQUID,
                asset=asset,
                order_id="",
                size=0,
                price=None,
                status="FAILED",
                message=str(e),
                timestamp=datetime.utcnow().isoformat()
            )

    # ========================================================================
    # Market Data
    # ========================================================================

    async def get_price(self, asset: str) -> Optional[float]:
        """
        Get current price from primary exchange (Hyperliquid).

        Args:
            asset: Asset identifier

        Returns:
            Current price or None
        """
        try:
            price = await self.hl_client.get_price(asset)
            return price
        except Exception as e:
            logger.error(f"Failed to get price for {asset}: {e}")
            return None

    async def get_prices(self, assets: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple assets.

        Args:
            assets: List of asset identifiers

        Returns:
            Dictionary of {asset: price}
        """
        try:
            prices = await self.hl_client.get_market_prices()
            return {asset: prices.get(asset) for asset in assets if asset in prices}
        except Exception as e:
            logger.error(f"Failed to get prices: {e}")
            return {}

    # ========================================================================
    # Allocation Management
    # ========================================================================

    async def _select_exchange_for_order(self, size: float) -> ExchangeType:
        """
        Select exchange for order based on allocation targets.

        Args:
            size: Order size

        Returns:
            Exchange to use for order
        """
        try:
            positions = await self.get_all_positions()
            hl_notional = sum(
                abs(p["size"] * p["current_price"])
                for p in positions["hyperliquid"]
            )
            cb_notional = sum(
                abs(p["size"] * p["current_price"])
                for p in positions["coinbase"]
            )

            total_notional = hl_notional + cb_notional

            # If Hyperliquid is below target allocation, use it
            hl_actual = (hl_notional / total_notional) if total_notional > 0 else 0
            if hl_actual < self.hl_allocation:
                return ExchangeType.HYPERLIQUID
            else:
                return ExchangeType.COINBASE

        except Exception as e:
            logger.warning(f"Failed to select exchange, defaulting to Hyperliquid: {e}")
            return ExchangeType.HYPERLIQUID

    async def get_allocation_status(self) -> Dict[str, Dict]:
        """
        Get current allocation across exchanges.

        Returns:
            Allocation status with target vs actual
        """
        try:
            positions = await self.get_all_positions()

            hl_notional = sum(
                abs(p["size"] * p["current_price"])
                for p in positions["hyperliquid"]
            )
            cb_notional = sum(
                abs(p["size"] * p["current_price"])
                for p in positions["coinbase"]
            )

            total_notional = hl_notional + cb_notional

            hl_actual = (hl_notional / total_notional) if total_notional > 0 else 0
            cb_actual = (cb_notional / total_notional) if total_notional > 0 else 0

            return {
                "hyperliquid": {
                    "target": self.hl_allocation,
                    "actual": hl_actual,
                    "drift": abs(hl_actual - self.hl_allocation),
                    "notional_value": hl_notional
                },
                "coinbase": {
                    "target": self.cb_allocation,
                    "actual": cb_actual,
                    "drift": abs(cb_actual - self.cb_allocation),
                    "notional_value": cb_notional
                },
                "total_notional": total_notional,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get allocation status: {e}")
            raise
