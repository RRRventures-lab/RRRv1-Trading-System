"""
Position Management Endpoints for RRRv1 API

Provides endpoints for:
- Position lifecycle management (open, close, reduce)
- Position monitoring and analytics
- Reconciliation status and history
- Risk monitoring
"""

from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
import logging

from position_manager import PositionManager, Position, PositionStatus, ReconciliationStatus
from exchange_reconciler import ExchangeReconciliationManager

logger = logging.getLogger(__name__)


def setup_position_endpoints(app: FastAPI,
                           position_manager: PositionManager,
                           reconciler: Optional[ExchangeReconciliationManager] = None):
    """
    Setup position management endpoints on FastAPI app.

    Args:
        app: FastAPI application
        position_manager: PositionManager instance
        reconciler: ExchangeReconciliationManager instance
    """

    # ========================================================================
    # Position Status & Monitoring
    # ========================================================================

    @app.get("/api/positions/summary")
    async def get_positions_summary(api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))):
        """Get summary of all positions"""
        try:
            summary = position_manager.get_portfolio_summary()
            return {
                'summary': summary,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get position summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/positions/active")
    async def get_active_positions(api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))):
        """Get all active positions with full details"""
        try:
            positions = position_manager.get_all_positions()
            return {
                'positions': [pos.to_dict() for pos in positions],
                'count': len(positions),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get active positions: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/positions/{asset}")
    async def get_position(asset: str, api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))):
        """Get details for specific position"""
        try:
            position = position_manager.get_position(asset)
            if not position:
                raise HTTPException(status_code=404, detail=f"Position {asset} not found")

            return {
                'position': position.to_dict(),
                'pnl': position.calculate_pnl(),
                'pnl_percent': position.calculate_pnl_percent(),
                'liquidation_distance': position.calculate_liquidation_distance(),
                'at_risk': position.is_liquidation_risk(),
                'margin_ratio': position.get_margin_ratio(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get position {asset}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/positions/at-risk")
    async def get_positions_at_risk(
        threshold: float = 5.0,
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Get positions near liquidation"""
        try:
            at_risk = position_manager.get_positions_at_risk(threshold)
            return {
                'positions': [pos.to_dict() for pos in at_risk],
                'count': len(at_risk),
                'threshold_pct': threshold,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get at-risk positions: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Position Lifecycle
    # ========================================================================

    @app.post("/api/positions/open")
    async def open_position(
        asset: str,
        entry_price: float,
        size: float,
        leverage: float = 1.0,
        venue: str = "hyperliquid",
        liquidation_price: Optional[float] = None,
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Open a new position"""
        try:
            position = Position(
                asset=asset,
                entry_price=entry_price,
                current_price=entry_price,
                size=size,
                leverage=leverage,
                venue=venue,
                status=PositionStatus.OPENING,
                liquidation_price=liquidation_price,
                opened_at=datetime.utcnow().isoformat()
            )

            position_manager.add_position(position)

            logger.info(f"Position opened: {asset} (size: {size}, price: {entry_price})")

            return {
                'status': 'success',
                'position': position.to_dict(),
                'message': f'Position {asset} opened',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to open position {asset}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/positions/{asset}/close")
    async def close_position(
        asset: str,
        close_price: float,
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Close an open position"""
        try:
            closed = position_manager.close_position(asset, close_price)

            if not closed:
                raise HTTPException(status_code=404, detail=f"Position {asset} not found")

            pnl = closed.calculate_pnl()
            pnl_percent = closed.calculate_pnl_percent()

            logger.info(f"Position closed: {asset} (P&L: {pnl:.2f} / {pnl_percent:.2f}%)")

            return {
                'status': 'success',
                'position': closed.to_dict(),
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'message': f'Position {asset} closed',
                'timestamp': datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to close position {asset}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/positions/{asset}/reduce")
    async def reduce_position(
        asset: str,
        reduction_size: float,
        reduction_price: float,
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Reduce an open position"""
        try:
            reduced = position_manager.reduce_position(asset, reduction_size, reduction_price)

            if not reduced:
                raise HTTPException(status_code=404, detail=f"Position {asset} not found")

            partial_pnl = (reduction_price - reduced.entry_price) * reduction_size

            logger.info(f"Position reduced: {asset} (reduced by: {reduction_size}, P&L: {partial_pnl:.2f})")

            return {
                'status': 'success',
                'position': reduced.to_dict(),
                'reduced_amount': reduction_size,
                'partial_pnl': partial_pnl,
                'message': f'Position {asset} reduced by {reduction_size}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to reduce position {asset}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Position History & Analytics
    # ========================================================================

    @app.get("/api/positions/{asset}/history")
    async def get_position_history(
        asset: str,
        limit: int = 50,
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Get change history for position"""
        try:
            history = position_manager.get_position_history(asset, limit)

            return {
                'asset': asset,
                'history': history,
                'count': len(history),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get position history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Reconciliation Status
    # ========================================================================

    @app.get("/api/reconciliation/status")
    async def get_reconciliation_status(
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Get reconciliation status for all positions"""
        try:
            positions = position_manager.get_all_positions()

            synced = len([p for p in positions if p.reconciliation_status == ReconciliationStatus.SYNCED])
            drifts = len([p for p in positions if p.reconciliation_status == ReconciliationStatus.DRIFT_DETECTED])
            pending = len([p for p in positions if p.reconciliation_status == ReconciliationStatus.PENDING_SYNC])

            return {
                'total_positions': len(positions),
                'synced': synced,
                'drift_detected': drifts,
                'pending_sync': pending,
                'position_details': [
                    {
                        'asset': p.asset,
                        'status': p.reconciliation_status.value,
                        'last_reconciled': p.last_reconciled_at
                    }
                    for p in positions
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get reconciliation status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/reconciliation/sync")
    async def sync_with_exchanges(
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Trigger reconciliation with exchanges"""
        try:
            if not reconciler:
                raise HTTPException(status_code=503, detail="Reconciler not initialized")

            result = await reconciler.reconcile_all()

            logger.info("Exchange reconciliation triggered")

            return {
                'status': 'success',
                'reconciliation': result,
                'message': 'Reconciliation triggered',
                'timestamp': datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to sync with exchanges: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/reconciliation/last")
    async def get_last_reconciliation(
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Get results of last reconciliation"""
        try:
            if not reconciler:
                raise HTTPException(status_code=503, detail="Reconciler not initialized")

            last = reconciler.get_last_reconciliation()

            if not last:
                raise HTTPException(status_code=404, detail="No reconciliation has been performed yet")

            return {
                'last_reconciliation': last,
                'timestamp': datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get last reconciliation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/reconciliation/allocation")
    async def validate_allocation(
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Validate allocation across exchanges"""
        try:
            if not reconciler:
                raise HTTPException(status_code=503, detail="Reconciler not initialized")

            # Get portfolio value (would come from agent in real system)
            portfolio_value = 10000.0  # Default for now

            result = await reconciler.validate_allocation(portfolio_value)

            return {
                'allocation_status': result,
                'timestamp': datetime.utcnow().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to validate allocation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/reconciliation/drift-history")
    async def get_drift_history(
        limit: int = 10,
        api_key: str = Depends(app.dependency_cache.get('check_rate_limit'))
    ):
        """Get history of detected allocation drift"""
        try:
            if not reconciler:
                raise HTTPException(status_code=503, detail="Reconciler not initialized")

            history = reconciler.get_drift_history(limit)

            return {
                'drift_events': history,
                'count': len(history),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get drift history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("Position management endpoints registered")
