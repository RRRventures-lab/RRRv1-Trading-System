"""
Coinbase Advanced Trade API Integration

Handles:
- REST API communication with Coinbase
- Order placement and management
- Position tracking (margin/spot)
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
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by Coinbase"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


@dataclass
class CoinbaseOrder:
    """Represents a Coinbase order"""
    order_id: str
    product_id: str
    side: OrderSide
    order_type: OrderType
    size: float
    price: Optional[float]
    status: OrderStatus
    filled_size: float
    average_filled_price: Optional[float]
    created_time: str
    updated_time: str


@dataclass
class CoinbasePosition:
    """Represents a margin/leveraged position on Coinbase"""
    product_id: str
    size: float
    entry_price: float
    current_price: float
    leverage: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    timestamp: str


@dataclass
class CoinbaseBalance:
    """Account balance information"""
    total_balance: float
    available_balance: float
    margin_balance: float
    margin_available: float
    timestamp: str


class CoinbaseAPIClient:
    """
    Coinbase Advanced Trade API Client

    Provides methods for:
    - REST API communication
    - Order placement and management
    - Account information
    - Market data
    - Portfolio management
    """

    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 request_timeout: float = 10.0):
        """
        Initialize Coinbase API client.

        Args:
            api_key: Coinbase API key
            api_secret: Coinbase API secret
            request_timeout: HTTP request timeout in seconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_timeout = request_timeout
        self.base_url = "https://api.exchange.coinbase.com"

        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info("Coinbase API client initialized")

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
            logger.info("Connected to Coinbase API")

    async def disconnect(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from Coinbase API")

    def _generate_signature(self,
                           request_path: str,
                           body: str,
                           timestamp: str,
                           method: str) -> str:
        """
        Generate HMAC-SHA256 signature for API request.

        Args:
            request_path: API endpoint path
            body: Request body JSON string
            timestamp: Request timestamp
            method: HTTP method

        Returns:
            Signature string
        """
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

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
        body_str = json.dumps(body) if body else ""
        timestamp = str(int(time.time()))

        signature = self._generate_signature(path, body_str, timestamp, method)

        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
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
                        logger.error(f"API error ({response.status}): {data}")
                        raise Exception(f"API error: {data}")
                    return data

            elif method == "POST":
                async with self.session.post(
                    url,
                    json=body or {},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.request_timeout)
                ) as response:
                    data = await response.json()
                    if response.status not in [200, 201]:
                        logger.error(f"API error ({response.status}): {data}")
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
            response = await self._request("GET", "/v1/accounts")
            logger.debug(f"Account info retrieved")
            return response
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    async def get_balance(self) -> CoinbaseBalance:
        """
        Get account balance.

        Returns:
            CoinbaseBalance object
        """
        try:
            accounts = await self.get_account_info()

            total_balance = sum(
                float(acc.get("balance", 0))
                for acc in accounts.get("accounts", [])
            )
            available_balance = sum(
                float(acc.get("available_balance", 0))
                for acc in accounts.get("accounts", [])
            )

            balance = CoinbaseBalance(
                total_balance=total_balance,
                available_balance=available_balance,
                margin_balance=total_balance,  # Simplified for now
                margin_available=available_balance,  # Simplified for now
                timestamp=datetime.utcnow().isoformat()
            )

            logger.debug(f"Balance: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    # ========================================================================
    # Position Operations (Margin/Leveraged)
    # ========================================================================

    async def get_open_positions(self) -> List[CoinbasePosition]:
        """
        Get all open margin/leveraged positions.

        Returns:
            List of CoinbasePosition objects
        """
        try:
            # Note: Endpoint depends on Coinbase API version
            response = await self._request("GET", "/v1/positions")

            positions = []
            for pos_data in response.get("positions", []):
                position = CoinbasePosition(
                    product_id=pos_data.get("product_id"),
                    size=float(pos_data.get("size", 0)),
                    entry_price=float(pos_data.get("entry_price", 0)),
                    current_price=float(pos_data.get("current_price", 0)),
                    leverage=float(pos_data.get("leverage", 1)),
                    unrealized_pnl=float(pos_data.get("unrealized_pnl", 0)),
                    unrealized_pnl_pct=float(pos_data.get("unrealized_pnl_pct", 0)),
                    timestamp=datetime.utcnow().isoformat()
                )
                positions.append(position)

            logger.info(f"Retrieved {len(positions)} open positions")
            return positions
        except Exception as e:
            logger.error(f"Failed to get open positions: {e}")
            raise

    async def get_position(self, product_id: str) -> Optional[CoinbasePosition]:
        """
        Get specific margin position.

        Args:
            product_id: Product identifier (e.g., "BTC-USD")

        Returns:
            CoinbasePosition or None if not found
        """
        try:
            positions = await self.get_open_positions()
            for pos in positions:
                if pos.product_id == product_id:
                    return pos
            return None
        except Exception as e:
            logger.error(f"Failed to get position for {product_id}: {e}")
            raise

    # ========================================================================
    # Order Operations
    # ========================================================================

    async def place_order(self,
                         product_id: str,
                         side: OrderSide,
                         order_type: OrderType,
                         size: Optional[float] = None,
                         price: Optional[float] = None,
                         post_only: bool = False) -> CoinbaseOrder:
        """
        Place a new order.

        Args:
            product_id: Product to trade (e.g., "BTC-USD")
            side: BUY or SELL
            order_type: MARKET, LIMIT, or STOP
            size: Order size (required for MARKET and LIMIT)
            price: Price (required for LIMIT)
            post_only: Only post to order book (maker only)

        Returns:
            CoinbaseOrder object

        Raises:
            ValueError: On invalid parameters
            Exception: On API error
        """
        if order_type == OrderType.LIMIT and not price:
            raise ValueError("LIMIT orders require price parameter")

        if order_type in [OrderType.MARKET, OrderType.LIMIT] and not size:
            raise ValueError(f"{order_type.value} orders require size parameter")

        try:
            body = {
                "product_id": product_id,
                "side": side.value,
                "order_type": order_type.value,
                "post_only": post_only
            }

            if size:
                body["size"] = str(size)
            if price:
                body["price"] = str(price)

            response = await self._request("POST", "/v1/orders", body)

            order = CoinbaseOrder(
                order_id=response.get("order_id"),
                product_id=product_id,
                side=side,
                order_type=order_type,
                size=float(response.get("size", size or 0)),
                price=price,
                status=OrderStatus(response.get("status", "PENDING")),
                filled_size=float(response.get("filled_size", 0)),
                average_filled_price=response.get("average_filled_price"),
                created_time=response.get("created_time", ""),
                updated_time=response.get("updated_time", "")
            )

            logger.info(f"Order placed: {order.order_id} {side.value} {size} {product_id} @ {price}")
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
            response = await self._request(
                "POST",
                f"/v1/orders/{order_id}/cancel"
            )

            logger.info(f"Order cancelled: {order_id}")
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    async def get_open_orders(self, product_id: Optional[str] = None) -> List[CoinbaseOrder]:
        """
        Get all open orders, optionally filtered by product.

        Args:
            product_id: Optional product filter

        Returns:
            List of CoinbaseOrder objects
        """
        try:
            params = f"?product_id={product_id}" if product_id else ""
            response = await self._request("GET", f"/v1/orders{params}")

            orders = []
            for order_data in response.get("orders", []):
                order = CoinbaseOrder(
                    order_id=order_data.get("order_id"),
                    product_id=order_data.get("product_id"),
                    side=OrderSide(order_data.get("side")),
                    order_type=OrderType(order_data.get("order_type")),
                    size=float(order_data.get("size", 0)),
                    price=order_data.get("price"),
                    status=OrderStatus(order_data.get("status")),
                    filled_size=float(order_data.get("filled_size", 0)),
                    average_filled_price=order_data.get("average_filled_price"),
                    created_time=order_data.get("created_time", ""),
                    updated_time=order_data.get("updated_time", "")
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

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Get product information.

        Args:
            product_id: Product identifier (e.g., "BTC-USD")

        Returns:
            Product data dictionary
        """
        try:
            response = await self._request("GET", f"/v1/products/{product_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            raise

    async def get_price(self, product_id: str) -> Optional[float]:
        """
        Get current price for a product.

        Args:
            product_id: Product identifier

        Returns:
            Current price or None
        """
        try:
            product = await self.get_product(product_id)
            return float(product.get("price", 0))
        except Exception as e:
            logger.error(f"Failed to get price for {product_id}: {e}")
            return None

    async def get_orderbook(self, product_id: str, level: int = 1) -> Dict[str, Any]:
        """
        Get orderbook for a product.

        Args:
            product_id: Product identifier
            level: Detail level (1=best bid/ask, 2=top 50, 3=full)

        Returns:
            Orderbook data {bids, asks}
        """
        try:
            response = await self._request(
                "GET",
                f"/v1/products/{product_id}/book?level={level}"
            )

            return {
                "product_id": product_id,
                "bids": response.get("bids", []),
                "asks": response.get("asks", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get orderbook for {product_id}: {e}")
            raise

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def close_position(self, product_id: str) -> Optional[CoinbaseOrder]:
        """
        Close an open margin position.

        Args:
            product_id: Product to close

        Returns:
            Order object or None if no position
        """
        try:
            position = await self.get_position(product_id)
            if not position:
                logger.warning(f"No position to close for {product_id}")
                return None

            # Close with opposite side
            side = OrderSide.SELL if position.size > 0 else OrderSide.BUY
            size = abs(position.size)

            order = await self.place_order(
                product_id=product_id,
                side=side,
                order_type=OrderType.MARKET,
                size=size
            )

            logger.info(f"Position closed: {product_id} ({size} units)")
            return order

        except Exception as e:
            logger.error(f"Failed to close position for {product_id}: {e}")
            raise

    async def reduce_position(self,
                             product_id: str,
                             reduction_amount: float) -> Optional[CoinbaseOrder]:
        """
        Reduce an open margin position.

        Args:
            product_id: Product to reduce
            reduction_amount: Amount to reduce by

        Returns:
            Order object or None
        """
        try:
            position = await self.get_position(product_id)
            if not position:
                logger.warning(f"No position to reduce for {product_id}")
                return None

            if reduction_amount > abs(position.size):
                logger.warning(f"Reduction amount {reduction_amount} exceeds position size {position.size}")
                reduction_amount = abs(position.size)

            # Reduce with opposite side
            side = OrderSide.SELL if position.size > 0 else OrderSide.BUY

            order = await self.place_order(
                product_id=product_id,
                side=side,
                order_type=OrderType.MARKET,
                size=reduction_amount
            )

            logger.info(f"Position reduced: {product_id} (reduced by {reduction_amount})")
            return order

        except Exception as e:
            logger.error(f"Failed to reduce position for {product_id}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if API is accessible.

        Returns:
            True if API is accessible
        """
        try:
            response = await self._request("GET", "/v1/products")
            is_healthy = isinstance(response, list) and len(response) > 0

            if is_healthy:
                logger.debug("Coinbase API health check: OK")
            else:
                logger.warning("Coinbase API health check: FAILED")

            return is_healthy
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
