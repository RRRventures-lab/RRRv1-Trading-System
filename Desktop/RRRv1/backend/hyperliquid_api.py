"""
Hyperliquid Exchange API Integration

Handles:
- REST API communication with Hyperliquid
- Order placement and management
- Position tracking
- Market data fetching
- Account information
- Signature generation and authentication
"""

import asyncio
import logging
import hmac
import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by Hyperliquid"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT_MARKET = "take_profit_market"
    TAKE_PROFIT_LIMIT = "take_profit_limit"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order execution status"""
    OPEN = "open"
    FILLED = "filled"
    PARTIAL = "partial_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class HyperliquidOrder:
    """Represents a Hyperliquid order"""
    order_id: str
    asset: str
    side: OrderSide
    order_type: OrderType
    size: float
    price: Optional[float]
    leverage: float
    status: OrderStatus
    filled: float
    remaining: float
    avg_fill_price: Optional[float]
    timestamp: str
    created_at: str
    updated_at: str


@dataclass
class HyperliquidPosition:
    """Represents a position on Hyperliquid"""
    asset: str
    size: float
    entry_price: float
    current_price: float
    leverage: float
    liquidation_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    margin_used: float
    timestamp: str


@dataclass
class HyperliquidBalance:
    """Account balance information"""
    total_balance: float
    available_balance: float
    used_balance: float
    portfolio_value: float
    timestamp: str


class HyperliquidAPIClient:
    """
    Hyperliquid Exchange API Client

    Provides methods for:
    - REST API communication
    - Order placement and management
    - Position tracking
    - Market data
    - Account information
    """

    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 testnet: bool = False,
                 request_timeout: float = 10.0):
        """
        Initialize Hyperliquid API client.

        Args:
            api_key: Hyperliquid API key
            api_secret: Hyperliquid API secret
            testnet: Use testnet instead of mainnet
            request_timeout: HTTP request timeout in seconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.request_timeout = request_timeout

        # API endpoints
        if testnet:
            self.base_url = "https://testnet.hyperliquid.xyz"
            logger.info("Using Hyperliquid TESTNET")
        else:
            self.base_url = "https://api.hyperliquid.xyz"
            logger.info("Using Hyperliquid MAINNET")

        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        self._nonce_offset = 0

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self) -> None:
        """Create HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.info("Connected to Hyperliquid API")

    async def disconnect(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from Hyperliquid API")

    def _generate_signature(self, request_path: str, body: Dict) -> Tuple[str, int]:
        """
        Generate HMAC-SHA256 signature for API request.

        Args:
            request_path: API endpoint path
            body: Request body dictionary

        Returns:
            Tuple of (signature, timestamp)
        """
        # Get nonce (timestamp in milliseconds)
        timestamp = int(time.time() * 1000) + self._nonce_offset
        self._nonce_offset += 1

        # Prepare message to sign
        msg = json.dumps({
            "method": request_path,
            "jsonrpc": "2.0",
            "id": timestamp,
            **body
        })

        # Generate signature
        signature = hmac.new(
            self.api_secret.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature, timestamp

    async def _request(self,
                      method: str,
                      path: str,
                      body: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated API request.

        Args:
            method: HTTP method (GET, POST)
            path: API endpoint path
            body: Request body for POST

        Returns:
            Response JSON

        Raises:
            Exception: On API error
        """
        if not self.session:
            raise RuntimeError("Not connected to API. Call connect() first.")

        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "HYPERLIQUID-KEY": self.api_key
        }

        try:
            if method == "GET":
                async with self.session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                ) as response:
                    data = await response.json()
                    if response.status != 200:
                        logger.error(f"API error: {data}")
                        raise Exception(f"API error: {data}")
                    return data

            elif method == "POST":
                # Sign request
                signature, timestamp = self._generate_signature(path, body or {})

                headers["HYPERLIQUID-SIGNATURE"] = signature
                headers["HYPERLIQUID-TIMESTAMP"] = str(timestamp)

                async with self.session.post(
                    url,
                    json=body or {},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                ) as response:
                    data = await response.json()
                    if response.status != 200:
                        logger.error(f"API error: {data}")
                        raise Exception(f"API error: {data}")
                    return data

            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except asyncio.TimeoutError:
            logger.error(f"API request timeout: {path}")
            raise
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise

    # ========================================================================
    # Account Information
    # ========================================================================

    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Account info dictionary
        """
        try:
            response = await self._request("GET", "/info/user/account")
            logger.debug(f"Account info: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    async def get_balance(self) -> HyperliquidBalance:
        """
        Get account balance.

        Returns:
            HyperliquidBalance object
        """
        try:
            response = await self._request("GET", "/info/user/balance")

            balance = HyperliquidBalance(
                total_balance=response.get("total_balance", 0),
                available_balance=response.get("available_balance", 0),
                used_balance=response.get("used_balance", 0),
                portfolio_value=response.get("portfolio_value", 0),
                timestamp=datetime.utcnow().isoformat()
            )

            logger.debug(f"Balance: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    # ========================================================================
    # Position Operations
    # ========================================================================

    async def get_open_positions(self) -> List[HyperliquidPosition]:
        """
        Get all open positions.

        Returns:
            List of HyperliquidPosition objects
        """
        try:
            response = await self._request("GET", "/info/user/open_positions")

            positions = []
            for pos_data in response.get("positions", []):
                position = HyperliquidPosition(
                    asset=pos_data.get("asset"),
                    size=float(pos_data.get("size", 0)),
                    entry_price=float(pos_data.get("entry_price", 0)),
                    current_price=float(pos_data.get("current_price", 0)),
                    leverage=float(pos_data.get("leverage", 1)),
                    liquidation_price=float(pos_data.get("liquidation_price", 0)),
                    unrealized_pnl=float(pos_data.get("unrealized_pnl", 0)),
                    unrealized_pnl_pct=float(pos_data.get("unrealized_pnl_pct", 0)),
                    margin_used=float(pos_data.get("margin_used", 0)),
                    timestamp=datetime.utcnow().isoformat()
                )
                positions.append(position)

            logger.info(f"Retrieved {len(positions)} open positions")
            return positions
        except Exception as e:
            logger.error(f"Failed to get open positions: {e}")
            raise

    async def get_position(self, asset: str) -> Optional[HyperliquidPosition]:
        """
        Get specific position.

        Args:
            asset: Asset identifier (e.g., "BTC")

        Returns:
            HyperliquidPosition or None if not found
        """
        try:
            positions = await self.get_open_positions()
            for pos in positions:
                if pos.asset == asset:
                    return pos
            return None
        except Exception as e:
            logger.error(f"Failed to get position for {asset}: {e}")
            raise

    # ========================================================================
    # Order Operations
    # ========================================================================

    async def place_order(self,
                         asset: str,
                         side: OrderSide,
                         size: float,
                         order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None,
                         leverage: float = 1.0,
                         reduce_only: bool = False) -> HyperliquidOrder:
        """
        Place a new order.

        Args:
            asset: Asset to trade (e.g., "BTC")
            side: BUY or SELL
            size: Order size
            order_type: Type of order (MARKET, LIMIT, etc.)
            price: Price (required for LIMIT orders)
            leverage: Leverage multiplier
            reduce_only: Only reduce existing position

        Returns:
            HyperliquidOrder object

        Raises:
            ValueError: On invalid parameters
            Exception: On API error
        """
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not price:
            raise ValueError(f"{order_type} order requires price parameter")

        try:
            body = {
                "action": "order",
                "asset": asset,
                "side": side.value,
                "size": size,
                "order_type": order_type.value,
                "leverage": leverage,
                "reduce_only": reduce_only
            }

            if price:
                body["price"] = price

            response = await self._request("POST", "/order/new", body)

            order = HyperliquidOrder(
                order_id=response.get("order_id"),
                asset=asset,
                side=side,
                order_type=order_type,
                size=size,
                price=price,
                leverage=leverage,
                status=OrderStatus(response.get("status", "open")),
                filled=float(response.get("filled", 0)),
                remaining=float(response.get("remaining", size)),
                avg_fill_price=response.get("avg_fill_price"),
                timestamp=datetime.utcnow().isoformat(),
                created_at=response.get("created_at", ""),
                updated_at=response.get("updated_at", "")
            )

            logger.info(f"Order placed: {order_id} {side.value} {size} {asset} @ {price}")
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order identifier

        Returns:
            True if cancelled successfully
        """
        try:
            body = {
                "action": "cancel_order",
                "order_id": order_id
            }

            response = await self._request("POST", "/order/cancel", body)

            logger.info(f"Order cancelled: {order_id}")
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    async def get_open_orders(self, asset: Optional[str] = None) -> List[HyperliquidOrder]:
        """
        Get all open orders, optionally filtered by asset.

        Args:
            asset: Optional asset filter

        Returns:
            List of HyperliquidOrder objects
        """
        try:
            path = f"/info/user/open_orders{f'/{asset}' if asset else ''}"
            response = await self._request("GET", path)

            orders = []
            for order_data in response.get("orders", []):
                order = HyperliquidOrder(
                    order_id=order_data.get("order_id"),
                    asset=order_data.get("asset"),
                    side=OrderSide(order_data.get("side")),
                    order_type=OrderType(order_data.get("order_type")),
                    size=float(order_data.get("size", 0)),
                    price=order_data.get("price"),
                    leverage=float(order_data.get("leverage", 1)),
                    status=OrderStatus(order_data.get("status")),
                    filled=float(order_data.get("filled", 0)),
                    remaining=float(order_data.get("remaining", 0)),
                    avg_fill_price=order_data.get("avg_fill_price"),
                    timestamp=datetime.utcnow().isoformat(),
                    created_at=order_data.get("created_at", ""),
                    updated_at=order_data.get("updated_at", "")
                )
                orders.append(order)

            logger.info(f"Retrieved {len(orders)} open orders")
            return orders
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise

    # ========================================================================
    # Market Data
    # ========================================================================

    async def get_market_prices(self) -> Dict[str, float]:
        """
        Get current market prices for all instruments.

        Returns:
            Dictionary of {asset: price}
        """
        try:
            response = await self._request("GET", "/info/markets/prices")

            prices = {
                item.get("asset"): float(item.get("price", 0))
                for item in response.get("prices", [])
            }

            logger.debug(f"Retrieved prices for {len(prices)} assets")
            return prices
        except Exception as e:
            logger.error(f"Failed to get market prices: {e}")
            raise

    async def get_price(self, asset: str) -> Optional[float]:
        """
        Get current price for a specific asset.

        Args:
            asset: Asset identifier

        Returns:
            Current price or None
        """
        try:
            prices = await self.get_market_prices()
            return prices.get(asset)
        except Exception as e:
            logger.error(f"Failed to get price for {asset}: {e}")
            return None

    async def get_orderbook(self, asset: str, depth: int = 20) -> Dict[str, Any]:
        """
        Get orderbook for an asset.

        Args:
            asset: Asset identifier
            depth: Orderbook depth (20-100)

        Returns:
            Orderbook data {bids, asks}
        """
        try:
            response = await self._request(
                "GET",
                f"/info/markets/orderbook/{asset}?depth={depth}"
            )

            return {
                "asset": asset,
                "bids": response.get("bids", []),
                "asks": response.get("asks", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {asset}: {e}")
            raise

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def close_position(self,
                            asset: str,
                            order_type: OrderType = OrderType.MARKET) -> Optional[HyperliquidOrder]:
        """
        Close an open position.

        Args:
            asset: Asset to close
            order_type: Type of close order (MARKET recommended)

        Returns:
            Order object or None if no position
        """
        try:
            position = await self.get_position(asset)
            if not position:
                logger.warning(f"No position to close for {asset}")
                return None

            # Close with opposite side
            side = OrderSide.SELL if position.size > 0 else OrderSide.BUY
            size = abs(position.size)

            order = await self.place_order(
                asset=asset,
                side=side,
                size=size,
                order_type=order_type,
                reduce_only=True
            )

            logger.info(f"Position closed: {asset} ({size} units)")
            return order

        except Exception as e:
            logger.error(f"Failed to close position for {asset}: {e}")
            raise

    async def reduce_position(self,
                             asset: str,
                             reduction_amount: float,
                             order_type: OrderType = OrderType.MARKET) -> Optional[HyperliquidOrder]:
        """
        Reduce an open position.

        Args:
            asset: Asset to reduce
            reduction_amount: Amount to reduce by
            order_type: Type of reduce order

        Returns:
            Order object or None
        """
        try:
            position = await self.get_position(asset)
            if not position:
                logger.warning(f"No position to reduce for {asset}")
                return None

            if reduction_amount > abs(position.size):
                logger.warning(f"Reduction amount {reduction_amount} exceeds position size {position.size}")
                reduction_amount = abs(position.size)

            # Reduce with opposite side
            side = OrderSide.SELL if position.size > 0 else OrderSide.BUY

            order = await self.place_order(
                asset=asset,
                side=side,
                size=reduction_amount,
                order_type=order_type,
                reduce_only=True
            )

            logger.info(f"Position reduced: {asset} (reduced by {reduction_amount})")
            return order

        except Exception as e:
            logger.error(f"Failed to reduce position for {asset}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if API is accessible.

        Returns:
            True if API is accessible
        """
        try:
            response = await self._request("GET", "/info/status")
            is_healthy = response.get("status") == "operational"

            if is_healthy:
                logger.debug("Hyperliquid API health check: OK")
            else:
                logger.warning(f"Hyperliquid API status: {response.get('status')}")

            return is_healthy
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
