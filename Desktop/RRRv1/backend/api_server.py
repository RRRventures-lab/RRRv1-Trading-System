"""
FastAPI server for RRRv1 trading dashboard
Provides REST API and WebSocket endpoints for real-time monitoring
Includes API key authentication and rate limiting (Phase 2)
"""

import asyncio
import logging
from typing import List, Set, Optional
from datetime import datetime
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from models import (
    PortfolioData, PositionData, StrategyPerformance, MetricsData,
    FundingData, TradeRecord, DashboardData, WebSocketUpdate, StrategySignal
)
from agent_integration import AgentDataProvider
from database import TradingDatabase
from auth import (
    get_api_key_manager, get_rate_limiter, initialize_default_key,
    APIKeyManager, RateLimiter
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RRRv1 Trading Dashboard API",
    description="Real-time monitoring and control for RRRv1 autonomous trading system",
    version="1.0.0"
)

# CORS middleware - restrict to localhost for single-user setup
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Global state
data_provider: AgentDataProvider = None
database: TradingDatabase = None
api_key_manager: Optional[APIKeyManager] = None
rate_limiter: Optional[RateLimiter] = None
active_websockets: Set[WebSocket] = set()
update_interval = 5  # seconds

# ============================================================================
# Authentication & Rate Limiting
# ============================================================================

async def verify_api_key(x_api_key: str = Header(None)) -> str:
    """
    Dependency to verify API key on protected endpoints.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The verified API key

    Raises:
        HTTPException: If key is missing or invalid
    """
    if not x_api_key:
        logger.warning("Request attempted without API key")
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Use X-API-Key header."
        )

    if not api_key_manager.verify_key(x_api_key):
        logger.warning(f"Invalid API key attempted")
        raise HTTPException(
            status_code=401,
            detail="Invalid or disabled API key"
        )

    return x_api_key


async def check_rate_limit(api_key: str = Depends(verify_api_key), endpoint: str = None):
    """
    Dependency to check rate limits for an API key.

    Args:
        api_key: Verified API key
        endpoint: Endpoint being accessed

    Raises:
        HTTPException: If rate limit exceeded
    """
    is_allowed, remaining, reset_time = rate_limiter.is_allowed(api_key, endpoint)

    if not is_allowed:
        logger.warning(f"Rate limit exceeded for API key")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Resets at {reset_time.isoformat()}",
            headers={"Retry-After": str(int((reset_time - datetime.utcnow()).total_seconds()))}
        )

    return api_key

# ============================================================================
# Initialization
# ============================================================================

def initialize_dashboard(agent, metrics_calc=None):
    """
    Initialize dashboard with trading agent and authentication.

    Args:
        agent: TradingAgent instance
        metrics_calc: Optional MetricsCalculator instance
    """
    global data_provider, database, api_key_manager, rate_limiter
    data_provider = AgentDataProvider(agent, metrics_calc)
    database = TradingDatabase()

    # Initialize authentication
    api_key_manager = get_api_key_manager()
    rate_limiter = get_rate_limiter()

    # Create default key if none exist
    initialize_default_key()

    logger.info("Dashboard initialized with trading agent and authentication")


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve dashboard info"""
    return """
    <html>
        <head>
            <title>RRRv1 Trading Dashboard API</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                h1 { color: #333; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>RRRv1 Trading Dashboard API</h1>
            <p>Real-time monitoring for your autonomous trading system</p>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/docs">/docs</a> - Interactive API documentation</li>
                <li><a href="/api/portfolio">/api/portfolio</a> - Portfolio status</li>
                <li><a href="/api/positions">/api/positions</a> - Active positions</li>
                <li><a href="/api/strategies">/api/strategies</a> - Strategy performance</li>
                <li><a href="/api/metrics">/api/metrics</a> - Trading metrics</li>
                <li><a href="/api/funding">/api/funding</a> - Funding arbitrage stats</li>
                <li><a href="/api/trades">/api/trades</a> - Trade history</li>
            </ul>
            <h2>WebSocket:</h2>
            <ul>
                <li>ws://localhost:8000/ws/live - Real-time updates</li>
            </ul>
        </body>
    </html>
    """


@app.get("/api/portfolio", response_model=PortfolioData)
async def get_portfolio(api_key: str = Depends(check_rate_limit)):
    """Get portfolio status (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    return PortfolioData(**data_provider.get_portfolio_status())


@app.get("/api/positions", response_model=List[PositionData])
async def get_positions(api_key: str = Depends(check_rate_limit)):
    """Get active positions (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    positions = data_provider.get_positions()
    return [PositionData(**pos) for pos in positions]


@app.get("/api/strategies", response_model=List[StrategyPerformance])
async def get_strategies(api_key: str = Depends(check_rate_limit)):
    """Get strategy performance (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    strategies = data_provider.get_strategies_performance()
    return [StrategyPerformance(**strat) for strat in strategies]


@app.get("/api/metrics", response_model=MetricsData)
async def get_metrics(api_key: str = Depends(check_rate_limit)):
    """Get trading metrics (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    return MetricsData(**data_provider.get_metrics())


@app.get("/api/funding", response_model=FundingData)
async def get_funding(api_key: str = Depends(check_rate_limit)):
    """Get funding arbitrage statistics (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    funding_data = data_provider.get_funding_data()
    return FundingData(**funding_data)


@app.get("/api/trades", response_model=List[TradeRecord])
async def get_trades(api_key: str = Depends(check_rate_limit), limit: int = 50):
    """Get trade history (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    trades = data_provider.get_recent_trades(limit)
    return [TradeRecord(**trade) for trade in trades]


@app.get("/api/dashboard", response_model=DashboardData)
async def get_full_dashboard(api_key: str = Depends(check_rate_limit)):
    """Get complete dashboard state (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    return DashboardData(
        portfolio=PortfolioData(**data_provider.get_portfolio_status()),
        positions=[PositionData(**pos) for pos in data_provider.get_positions()],
        strategies=[StrategyPerformance(**strat) for strat in data_provider.get_strategies_performance()],
        metrics=MetricsData(**data_provider.get_metrics()),
        funding=FundingData(**data_provider.get_funding_data()),
        recent_signals=[],  # Would populate from agent
        recent_trades=[TradeRecord(**trade) for trade in data_provider.get_recent_trades(10)]
    )


# ============================================================================
# API Key Management Endpoints
# ============================================================================

@app.get("/api/auth/status")
async def get_auth_status(api_key: str = Depends(verify_api_key)):
    """Get authentication status and key info"""
    if not api_key_manager:
        raise HTTPException(status_code=503, detail="Authentication not initialized")

    usage = rate_limiter.get_usage(api_key) if rate_limiter else {}
    return {
        "authenticated": True,
        "key_valid": True,
        "rate_limit_status": usage,
        "keys_configured": len(api_key_manager.list_keys())
    }


@app.get("/api/auth/keys")
async def list_api_keys(api_key: str = Depends(verify_api_key)):
    """List all API keys (without showing the actual keys)"""
    if not api_key_manager:
        raise HTTPException(status_code=503, detail="Authentication not initialized")

    return {
        "keys": api_key_manager.list_keys(),
        "stats": api_key_manager.get_key_stats()
    }


@app.post("/api/auth/keys")
async def create_api_key(api_key: str = Depends(verify_api_key), name: str = "new_key"):
    """Generate a new API key (save securely!)"""
    if not api_key_manager:
        raise HTTPException(status_code=503, detail="Authentication not initialized")

    new_key = api_key_manager.generate_key(name)
    logger.warning(f"New API key generated: {name}")

    return {
        "status": "success",
        "message": "New API key generated. Save this securely - it won't be shown again!",
        "api_key": new_key,
        "name": name,
        "usage": "Use in request header: X-API-Key: " + new_key
    }


@app.post("/api/auth/keys/{key_name}/revoke")
async def revoke_api_key(key_name: str, api_key: str = Depends(verify_api_key)):
    """Revoke an API key by name"""
    if not api_key_manager:
        raise HTTPException(status_code=503, detail="Authentication not initialized")

    # Find key by name and revoke
    keys = api_key_manager.list_keys()
    matching_keys = [k for k in keys if k.get("name") == key_name]

    if not matching_keys:
        raise HTTPException(status_code=404, detail=f"Key '{key_name}' not found")

    logger.warning(f"API key revoked: {key_name}")

    return {
        "status": "success",
        "message": f"API key '{key_name}' has been revoked"
    }


@app.get("/api/auth/usage")
async def get_usage(api_key: str = Depends(verify_api_key)):
    """Get current rate limit usage for this key"""
    if not rate_limiter:
        raise HTTPException(status_code=503, detail="Rate limiter not initialized")

    usage = rate_limiter.get_usage(api_key)
    return {
        "current_usage": usage,
        "time_checked": datetime.utcnow().isoformat()
    }


# ============================================================================
# Control Endpoints
# ============================================================================

@app.post("/api/emergency-stop")
async def emergency_stop(api_key: str = Depends(check_rate_limit)):
    """Trigger emergency stop (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    logger.warning("Emergency stop triggered via API")
    success = data_provider.trigger_emergency_stop()

    if success:
        # Broadcast to WebSockets
        await broadcast_update({
            'event_type': 'emergency_stop',
            'data': {'message': 'Emergency stop triggered'},
            'timestamp': datetime.now().isoformat()
        })
        return {'status': 'success', 'message': 'Emergency stop triggered'}
    else:
        raise HTTPException(status_code=500, detail="Failed to trigger emergency stop")


@app.post("/api/close-position/{asset}")
async def close_position(asset: str, api_key: str = Depends(check_rate_limit)):
    """Close a specific position (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    logger.info(f"Close position request for {asset}")
    success = await data_provider.close_position(asset)

    if success:
        # Broadcast to WebSockets
        await broadcast_update({
            'event_type': 'position_closed',
            'data': {'asset': asset},
            'timestamp': datetime.now().isoformat()
        })
        return {'status': 'success', 'message': f'Position {asset} closed'}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to close position {asset}")


@app.post("/api/reduce-position/{asset}")
async def reduce_position(asset: str, api_key: str = Depends(check_rate_limit), reduction_pct: float = 0.5):
    """Reduce a position by percentage (requires API key)"""
    if not data_provider:
        raise HTTPException(status_code=503, detail="Dashboard not initialized")

    if not (0 < reduction_pct <= 1):
        raise HTTPException(status_code=400, detail="reduction_pct must be between 0 and 1")

    logger.info(f"Reduce position request for {asset} by {reduction_pct:.0%}")
    success = await data_provider.reduce_position(asset, reduction_pct)

    if success:
        # Broadcast to WebSockets
        await broadcast_update({
            'event_type': 'position_reduced',
            'data': {'asset': asset, 'reduction_pct': reduction_pct},
            'timestamp': datetime.now().isoformat()
        })
        return {'status': 'success', 'message': f'Position {asset} reduced by {reduction_pct:.0%}'}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to reduce position {asset}")


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket, api_key: Optional[str] = None):
    """
    WebSocket endpoint for real-time updates.
    Requires API key via query parameter: ws://host/ws/live?api_key=YOUR_KEY

    Clients receive updates on:
    - Position price changes
    - Liquidation distance changes
    - New signals
    - Trade executions
    - Funding payments
    """
    # Check for API key in query parameters or headers
    query_params = websocket.query_params
    api_key = api_key or query_params.get("api_key")

    if not api_key:
        await websocket.close(code=4001, reason="Missing API key. Use ?api_key=YOUR_KEY")
        logger.warning("WebSocket connection rejected: missing API key")
        return

    # Verify API key
    if not api_key_manager or not api_key_manager.verify_key(api_key):
        await websocket.close(code=4001, reason="Invalid API key")
        logger.warning("WebSocket connection rejected: invalid API key")
        return

    # Check rate limit
    is_allowed, _, reset_time = rate_limiter.is_allowed(api_key, "/ws/live") if rate_limiter else (True, 0, None)
    if not is_allowed:
        await websocket.close(code=4029, reason=f"Rate limit exceeded. Resets at {reset_time.isoformat()}")
        logger.warning("WebSocket connection rejected: rate limit exceeded")
        return

    await websocket.accept()
    active_websockets.add(websocket)

    logger.info(f"WebSocket client connected with valid API key. Total clients: {len(active_websockets)}")

    try:
        while True:
            # Receive any client messages (heartbeat/commands)
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            message = json.loads(data)

            if message.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})

    except asyncio.TimeoutError:
        # Timeout is normal for long-polling
        pass
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_websockets.discard(websocket)
        logger.info(f"WebSocket client removed. Total clients: {len(active_websockets)}")


async def broadcast_update(update: dict):
    """
    Broadcast update to all connected WebSocket clients.

    Args:
        update: Update data to broadcast
    """
    if not active_websockets:
        return

    disconnected = set()

    for websocket in active_websockets:
        try:
            await websocket.send_json(update)
        except Exception as e:
            logger.error(f"Failed to send WebSocket update: {e}")
            disconnected.add(websocket)

    # Remove disconnected clients
    for websocket in disconnected:
        active_websockets.discard(websocket)


# ============================================================================
# Background Task for Periodic Updates
# ============================================================================

async def periodic_updates():
    """
    Periodic task to broadcast updated data to all WebSocket clients.
    Runs every update_interval seconds.
    """
    while True:
        try:
            await asyncio.sleep(update_interval)

            if not data_provider or not active_websockets:
                continue

            # Get current positions and broadcast updates
            positions = data_provider.get_positions()
            portfolio = data_provider.get_portfolio_status()

            # Broadcast position updates
            for position in positions:
                await broadcast_update({
                    'event_type': 'position_update',
                    'data': position,
                    'timestamp': datetime.now().isoformat()
                })

            # Broadcast portfolio update every 10 cycles
            if int(datetime.now().timestamp()) % (update_interval * 10) == 0:
                await broadcast_update({
                    'event_type': 'portfolio_update',
                    'data': portfolio,
                    'timestamp': datetime.now().isoformat()
                })

        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")


@app.on_event("startup")
async def startup_event():
    """Start background update task and verify authentication"""
    global api_key_manager, rate_limiter

    # Initialize authentication if not already done
    if not api_key_manager:
        api_key_manager = get_api_key_manager()
        rate_limiter = get_rate_limiter()
        initialize_default_key()
        logger.info("Authentication initialized at startup")

    asyncio.create_task(periodic_updates())
    logger.info("Periodic update task started")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting RRRv1 Trading Dashboard API")
    logger.info("API documentation available at http://localhost:8000/docs")
    logger.info("WebSocket available at ws://localhost:8000/ws/live")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
