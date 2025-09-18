#!/usr/bin/env python3
"""
Coinbase Advanced Trade API Integration
Real-time market data and trading interface
"""

import os
import json
import time
import hmac
import hashlib
import base64
import asyncio
import aiohttp
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

@dataclass
class CoinbaseCandle:
    timestamp: float
    low: float
    high: float
    open: float
    close: float
    volume: float

@dataclass
class CoinbaseTrade:
    trade_id: str
    product_id: str
    price: float
    size: float
    side: str
    time: datetime

@dataclass
class CoinbaseOrderBook:
    product_id: str
    bids: List[List[str]]
    asks: List[List[str]]
    time: datetime

class CoinbaseAdvancedTradeAPI:
    """Coinbase Advanced Trade API client with real-time data"""

    def __init__(self):
        self.api_key = os.getenv('COINBASE_API_KEY')
        self.api_secret = os.getenv('COINBASE_API_SECRET')
        self.base_url = 'https://api.coinbase.com'
        self.sandbox_url = 'https://api-public.sandbox.exchange.coinbase.com'
        self.websocket_url = 'wss://advanced-trade-ws.coinbase.com'
        self.use_sandbox = os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true'

        self.session = None
        self.websocket = None
        self.logger = logging.getLogger(__name__)

        # Real-time data storage
        self.live_prices = {}
        self.live_order_books = {}
        self.live_trades = []
        self.candles_data = {}

    def generate_signature(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        """Generate API signature for authenticated requests"""
        message = timestamp + method + path + body
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated API request"""
        timestamp = str(int(time.time()))
        path = f"/api/v3{endpoint}"

        body = json.dumps(data) if data else ''
        signature = self.generate_signature(timestamp, method.upper(), path, body)

        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}{path}"
        session = await self.get_session()

        try:
            async with session.request(method, url, headers=headers, params=params, json=data) as response:
                return await response.json()
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            return {}

    async def get_products(self) -> List[Dict]:
        """Get all available trading products"""
        response = await self.make_request('GET', '/brokerage/products')
        return response.get('products', [])

    async def get_product_candles(self, product_id: str, granularity: int = 300, limit: int = 100) -> List[CoinbaseCandle]:
        """Get historical candles for a product"""
        params = {
            'granularity': granularity,
            'limit': limit
        }

        response = await self.make_request('GET', f'/brokerage/products/{product_id}/candles', params=params)
        candles = []

        for candle_data in response.get('candles', []):
            candle = CoinbaseCandle(
                timestamp=float(candle_data['start']),
                low=float(candle_data['low']),
                high=float(candle_data['high']),
                open=float(candle_data['open']),
                close=float(candle_data['close']),
                volume=float(candle_data['volume'])
            )
            candles.append(candle)

        return candles

    async def get_product_ticker(self, product_id: str) -> Dict:
        """Get current ticker for a product"""
        response = await self.make_request('GET', f'/brokerage/products/{product_id}/ticker')
        return response

    async def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        response = await self.make_request('GET', '/brokerage/accounts')
        return response.get('accounts', [])

    async def create_order(self, product_id: str, side: str, size: str, order_type: str = 'market') -> Dict:
        """Create a trading order (paper trading simulation)"""
        # For paper trading, we'll simulate the order
        order_data = {
            'product_id': product_id,
            'side': side,
            'order_configuration': {
                'market_market_ioc': {
                    'base_size': size
                }
            }
        }

        # In paper trading mode, simulate the response
        if os.getenv('PAPER_TRADING', 'true').lower() == 'true':
            current_price = self.live_prices.get(product_id, 0)
            simulated_order = {
                'success': True,
                'order_id': f"paper_{int(time.time())}_{product_id}",
                'product_id': product_id,
                'side': side,
                'size': size,
                'price': current_price,
                'status': 'filled',
                'timestamp': datetime.now().isoformat()
            }
            self.logger.info(f"📄 Paper trade executed: {side} {size} {product_id} @ ${current_price}")
            return simulated_order
        else:
            # Real trading
            response = await self.make_request('POST', '/brokerage/orders', data=order_data)
            return response

    async def start_websocket_feed(self, product_ids: List[str]):
        """Start real-time WebSocket data feed"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)

            # Subscribe to multiple channels
            subscribe_message = {
                "type": "subscribe",
                "product_ids": product_ids,
                "channels": [
                    {
                        "name": "level2",
                        "product_ids": product_ids
                    },
                    {
                        "name": "ticker",
                        "product_ids": product_ids
                    },
                    {
                        "name": "matches",
                        "product_ids": product_ids
                    }
                ]
            }

            await self.websocket.send(json.dumps(subscribe_message))
            self.logger.info(f"🔗 WebSocket connected, subscribed to {product_ids}")

            # Start listening for messages
            asyncio.create_task(self.handle_websocket_messages())

        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")

    async def handle_websocket_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_websocket_message(data)
        except Exception as e:
            self.logger.error(f"WebSocket message handling error: {e}")

    async def process_websocket_message(self, data: Dict):
        """Process different types of WebSocket messages"""
        message_type = data.get('type')

        if message_type == 'ticker':
            # Update live prices
            product_id = data.get('product_id')
            price = float(data.get('price', 0))
            self.live_prices[product_id] = price

        elif message_type == 'l2update':
            # Update order book
            product_id = data.get('product_id')
            self.live_order_books[product_id] = {
                'bids': data.get('changes', []),
                'asks': data.get('changes', []),
                'time': datetime.now()
            }

        elif message_type == 'match':
            # New trade
            trade = CoinbaseTrade(
                trade_id=data.get('trade_id'),
                product_id=data.get('product_id'),
                price=float(data.get('price', 0)),
                size=float(data.get('size', 0)),
                side=data.get('side'),
                time=datetime.fromisoformat(data.get('time', '').replace('Z', '+00:00'))
            )
            self.live_trades.append(trade)

            # Keep only recent trades
            if len(self.live_trades) > 1000:
                self.live_trades = self.live_trades[-500:]

    async def get_live_price(self, product_id: str) -> float:
        """Get current live price"""
        return self.live_prices.get(product_id, 0.0)

    async def get_live_order_book(self, product_id: str) -> Optional[Dict]:
        """Get current order book"""
        return self.live_order_books.get(product_id)

    async def get_recent_trades(self, product_id: str, limit: int = 50) -> List[CoinbaseTrade]:
        """Get recent trades for a product"""
        product_trades = [t for t in self.live_trades if t.product_id == product_id]
        return product_trades[-limit:]

    async def close(self):
        """Close connections"""
        if self.websocket:
            await self.websocket.close()
        if self.session and not self.session.closed:
            await self.session.close()

class CoinbaseWebSocketServer:
    """WebSocket server for real-time frontend updates"""

    def __init__(self, coinbase_api: CoinbaseAdvancedTradeAPI, port: int = 8765):
        self.coinbase_api = coinbase_api
        self.port = port
        self.connected_clients = set()
        self.logger = logging.getLogger(__name__)

    async def register_client(self, websocket, path):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        self.logger.info(f"📱 Frontend client connected. Total clients: {len(self.connected_clients)}")

        try:
            # Send initial data
            await self.send_initial_data(websocket)

            # Keep connection alive and handle client messages
            async for message in websocket:
                await self.handle_client_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            self.logger.info(f"📱 Frontend client disconnected. Total clients: {len(self.connected_clients)}")

    async def send_initial_data(self, websocket):
        """Send initial data to newly connected client"""
        # Send current prices
        if self.coinbase_api.live_prices:
            await websocket.send(json.dumps({
                'type': 'initial_prices',
                'data': self.coinbase_api.live_prices
            }))

        # Send recent trades
        recent_trades = self.coinbase_api.live_trades[-50:] if self.coinbase_api.live_trades else []
        await websocket.send(json.dumps({
            'type': 'initial_trades',
            'data': [asdict(trade) for trade in recent_trades]
        }))

    async def handle_client_message(self, websocket, message):
        """Handle messages from frontend clients"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'request_data':
                product_id = data.get('product_id')
                if product_id:
                    # Send specific product data
                    await self.send_product_data(websocket, product_id)

        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")

    async def send_product_data(self, websocket, product_id: str):
        """Send specific product data to client"""
        # Current price
        price = await self.coinbase_api.get_live_price(product_id)

        # Order book
        order_book = await self.coinbase_api.get_live_order_book(product_id)

        # Recent trades
        trades = await self.coinbase_api.get_recent_trades(product_id, 20)

        await websocket.send(json.dumps({
            'type': 'product_data',
            'product_id': product_id,
            'price': price,
            'order_book': order_book,
            'trades': [asdict(trade) for trade in trades]
        }))

    async def broadcast_update(self, update_type: str, data: Any):
        """Broadcast update to all connected clients"""
        if self.connected_clients:
            message = json.dumps({
                'type': update_type,
                'data': data,
                'timestamp': time.time()
            })

            # Send to all connected clients
            disconnected_clients = set()
            for client in self.connected_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)

            # Remove disconnected clients
            self.connected_clients -= disconnected_clients

    async def start_price_broadcast(self):
        """Continuously broadcast price updates"""
        while True:
            try:
                if self.coinbase_api.live_prices and self.connected_clients:
                    await self.broadcast_update('price_update', self.coinbase_api.live_prices)
                await asyncio.sleep(0.1)  # 100ms updates
            except Exception as e:
                self.logger.error(f"Price broadcast error: {e}")
                await asyncio.sleep(1)

    async def start_server(self):
        """Start the WebSocket server"""
        self.logger.info(f"🚀 Starting WebSocket server on port {self.port}")

        # Start price broadcasting
        asyncio.create_task(self.start_price_broadcast())

        # Start WebSocket server
        await websockets.serve(self.register_client, "localhost", self.port)
        self.logger.info(f"📡 WebSocket server running on ws://localhost:{self.port}")

async def main():
    """Main function for testing Coinbase API integration"""
    # Initialize Coinbase API
    coinbase_api = CoinbaseAdvancedTradeAPI()

    # Start WebSocket feed for major crypto pairs
    products = ['BTC-USD', 'ETH-USD', 'SOL-USD']

    try:
        # Start Coinbase WebSocket feed
        await coinbase_api.start_websocket_feed(products)

        # Start WebSocket server for frontend
        ws_server = CoinbaseWebSocketServer(coinbase_api)
        await ws_server.start_server()

        # Keep running
        await asyncio.sleep(3600)  # Run for 1 hour

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        await coinbase_api.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())