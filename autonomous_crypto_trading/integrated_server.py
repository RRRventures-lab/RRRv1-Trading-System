#!/usr/bin/env python3
"""
Integrated Trading Server
Combines multi-agent system with real-time frontend dashboard
"""

import asyncio
import json
import logging
import time
import websockets
from typing import Set, Dict, Any
from datetime import datetime
import threading
from dataclasses import asdict

# Import our trading systems
from multi_agent_system import MultiAgentOrchestrator
from coinbase_api import CoinbaseAdvancedTradeAPI, CoinbaseWebSocketServer

class IntegratedTradingServer:
    """Integrated server combining trading system with real-time dashboard"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize trading components
        self.trading_orchestrator = MultiAgentOrchestrator()
        self.coinbase_api = CoinbaseAdvancedTradeAPI()

        # WebSocket server for frontend
        self.frontend_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.dashboard_server_port = 8765

        # Real-time data storage
        self.live_data = {
            'portfolio': {
                'total_value': 2500,
                'cash': 2500,
                'positions': {},
                'daily_return': 0,
                'total_return': 0,
            },
            'agents': [],
            'signals': [],
            'trades': [],
            'system_metrics': {
                'signals_per_second': 0,
                'executed_trades': 0,
                'total_signals': 0,
                'uptime': 0,
                'cpu_usage': 0,
                'memory_usage': 0,
                'active_agents': 9,
            },
            'market_data': {}
        }

        # Performance tracking
        self.start_time = time.time()
        self.signal_count = 0
        self.trade_count = 0

    async def start_coinbase_feed(self):
        """Start Coinbase real-time data feed"""
        try:
            products = ['BTC-USD', 'ETH-USD', 'SOL-USD']
            await self.coinbase_api.start_websocket_feed(products)
            self.logger.info("🔗 Coinbase data feed started")
        except Exception as e:
            self.logger.error(f"Failed to start Coinbase feed: {e}")

    async def start_trading_system(self):
        """Start the multi-agent trading system"""
        try:
            # Start trading system in background
            trading_task = asyncio.create_task(self.trading_orchestrator.run_ultra_fast_cycle())
            self.logger.info("🤖 Multi-agent trading system started")

            # Monitor and relay trading data
            monitor_task = asyncio.create_task(self.monitor_trading_system())

            return trading_task, monitor_task
        except Exception as e:
            self.logger.error(f"Failed to start trading system: {e}")

    async def monitor_trading_system(self):
        """Monitor trading system and relay data to frontend"""
        while True:
            try:
                # Update system metrics
                uptime = time.time() - self.start_time
                signals_per_second = self.signal_count / max(uptime, 1)

                self.live_data['system_metrics'].update({
                    'uptime': uptime,
                    'signals_per_second': signals_per_second,
                    'executed_trades': self.trade_count,
                    'total_signals': self.signal_count,
                })

                # Get agent performance data
                agent_data = []
                for agent in self.trading_orchestrator.agents:
                    agent_info = {
                        'agent_id': agent.agent_id,
                        'strategy_name': agent.strategy_name,
                        'status': 'active',
                        'performance': asdict(agent.performance) if hasattr(agent, 'performance') else {
                            'agent_id': agent.agent_id,
                            'total_trades': 0,
                            'win_rate': 0.0,
                            'avg_return': 0.0,
                            'sharpe_ratio': 0.0,
                            'max_drawdown': 0.0,
                            'confidence_accuracy': 0.0,
                            'last_updated': datetime.now().isoformat(),
                        }
                    }
                    agent_data.append(agent_info)

                self.live_data['agents'] = agent_data

                # Get portfolio data from execution engine
                if hasattr(self.trading_orchestrator, 'execution_engine'):
                    portfolio_value = await self.trading_orchestrator.execution_engine.get_portfolio_value()
                    self.live_data['portfolio']['total_value'] = portfolio_value

                # Get market data from Coinbase
                self.live_data['market_data'] = {
                    'BTC-USD': {
                        'symbol': 'BTC-USD',
                        'price': await self.coinbase_api.get_live_price('BTC-USD') or 45000,
                        'change_24h': 0,
                        'change_percent_24h': 0,
                        'volume_24h': 0,
                        'market_cap': 0,
                        'last_updated': datetime.now().isoformat(),
                    },
                    'ETH-USD': {
                        'symbol': 'ETH-USD',
                        'price': await self.coinbase_api.get_live_price('ETH-USD') or 2800,
                        'change_24h': 0,
                        'change_percent_24h': 0,
                        'volume_24h': 0,
                        'market_cap': 0,
                        'last_updated': datetime.now().isoformat(),
                    },
                    'SOL-USD': {
                        'symbol': 'SOL-USD',
                        'price': await self.coinbase_api.get_live_price('SOL-USD') or 95,
                        'change_24h': 0,
                        'change_percent_24h': 0,
                        'volume_24h': 0,
                        'market_cap': 0,
                        'last_updated': datetime.now().isoformat(),
                    }
                }

                # Broadcast updates to frontend clients
                await self.broadcast_to_frontend('system_update', self.live_data)

                await asyncio.sleep(1)  # Update every second

            except Exception as e:
                self.logger.error(f"Error monitoring trading system: {e}")
                await asyncio.sleep(5)

    async def start_frontend_websocket_server(self):
        """Start WebSocket server for frontend dashboard"""
        async def handle_frontend_client(websocket, path):
            """Handle frontend WebSocket connections"""
            self.frontend_clients.add(websocket)
            self.logger.info(f"📱 Frontend client connected. Total: {len(self.frontend_clients)}")

            try:
                # Send initial data
                await websocket.send(json.dumps({
                    'type': 'initial_data',
                    'data': self.live_data,
                    'timestamp': time.time()
                }))

                # Handle client messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_frontend_message(websocket, data)
                    except Exception as e:
                        self.logger.error(f"Error handling frontend message: {e}")

            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception as e:
                self.logger.error(f"Frontend client error: {e}")
            finally:
                self.frontend_clients.discard(websocket)
                self.logger.info(f"📱 Frontend client disconnected. Total: {len(self.frontend_clients)}")

        # Start WebSocket server
        server = await websockets.serve(
            handle_frontend_client,
            "localhost",
            self.dashboard_server_port
        )

        self.logger.info(f"📡 Frontend WebSocket server started on ws://localhost:{self.dashboard_server_port}")
        return server

    async def handle_frontend_message(self, websocket, data: Dict[str, Any]):
        """Handle messages from frontend clients"""
        message_type = data.get('type')

        if message_type == 'request_data':
            # Send current data
            await websocket.send(json.dumps({
                'type': 'data_update',
                'data': self.live_data,
                'timestamp': time.time()
            }))

        elif message_type == 'agent_command':
            # Handle agent control commands
            agent_id = data.get('agent_id')
            command = data.get('command')

            if command == 'pause':
                # Implement agent pause logic
                self.logger.info(f"Pausing agent {agent_id}")
            elif command == 'resume':
                # Implement agent resume logic
                self.logger.info(f"Resuming agent {agent_id}")

    async def broadcast_to_frontend(self, message_type: str, data: Any):
        """Broadcast data to all connected frontend clients"""
        if not self.frontend_clients:
            return

        message = json.dumps({
            'type': message_type,
            'data': data,
            'timestamp': time.time()
        })

        # Send to all connected clients
        disconnected_clients = set()
        for client in self.frontend_clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.frontend_clients -= disconnected_clients

    async def simulate_trading_activity(self):
        """Simulate trading activity for demonstration"""
        import random

        while True:
            try:
                # Simulate signal generation
                if random.random() < 0.3:  # 30% chance per second
                    signal = {
                        'agent_id': random.choice(['SCALPER_001', 'CLAUDE_DEEP_001', 'COMPETITIVE_001']),
                        'symbol': random.choice(['BTC-USD', 'ETH-USD', 'SOL-USD']),
                        'action': random.choice(['buy', 'sell']),
                        'confidence': random.uniform(0.6, 0.95),
                        'strategy': 'simulated',
                        'price': random.uniform(40000, 50000) if 'BTC' in 'BTC-USD' else random.uniform(2500, 3000),
                        'timestamp': datetime.now().isoformat(),
                        'reasoning': 'Simulated trading signal for demonstration',
                        'risk_score': random.uniform(0.1, 0.5),
                        'expected_return': random.uniform(0.001, 0.02),
                        'timeframe': random.choice(['scalp', 'short', 'medium']),
                    }

                    self.live_data['signals'].insert(0, signal)
                    self.live_data['signals'] = self.live_data['signals'][:50]  # Keep only recent signals
                    self.signal_count += 1

                    # Broadcast signal update
                    await self.broadcast_to_frontend('signal_generated', signal)

                # Simulate trade execution
                if random.random() < 0.1:  # 10% chance per second
                    trade = {
                        'id': f"trade_{int(time.time())}_{random.randint(1000, 9999)}",
                        'symbol': random.choice(['BTC-USD', 'ETH-USD', 'SOL-USD']),
                        'side': random.choice(['buy', 'sell']),
                        'quantity': random.uniform(0.001, 0.1),
                        'price': random.uniform(40000, 50000) if 'BTC' in random.choice(['BTC-USD', 'ETH-USD', 'SOL-USD']) else random.uniform(2500, 3000),
                        'timestamp': datetime.now().isoformat(),
                        'agent_id': random.choice(['SCALPER_001', 'CLAUDE_DEEP_001', 'COMPETITIVE_001']),
                        'strategy': 'simulated',
                        'pnl': random.uniform(-50, 100),
                    }

                    self.live_data['trades'].insert(0, trade)
                    self.live_data['trades'] = self.live_data['trades'][:100]  # Keep only recent trades
                    self.trade_count += 1

                    # Broadcast trade update
                    await self.broadcast_to_frontend('trade_executed', trade)

                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in simulation: {e}")
                await asyncio.sleep(5)

    async def run(self):
        """Run the integrated trading server"""
        self.logger.info("🚀 Starting Integrated Trading Server")

        try:
            # Start all components
            tasks = []

            # Start Coinbase data feed
            coinbase_task = asyncio.create_task(self.start_coinbase_feed())
            tasks.append(coinbase_task)

            # Start trading system
            trading_tasks = await self.start_trading_system()
            if trading_tasks:
                tasks.extend(trading_tasks)

            # Start frontend WebSocket server
            frontend_server = await self.start_frontend_websocket_server()

            # Start activity simulation (for demo)
            simulation_task = asyncio.create_task(self.simulate_trading_activity())
            tasks.append(simulation_task)

            self.logger.info("✅ All systems started successfully")
            self.logger.info(f"📊 Dashboard available at: http://localhost:3000")
            self.logger.info(f"📡 WebSocket server: ws://localhost:{self.dashboard_server_port}")

            # Keep running
            await asyncio.gather(*tasks, return_exceptions=True)

        except KeyboardInterrupt:
            self.logger.info("🛑 Shutting down...")
        except Exception as e:
            self.logger.error(f"💥 Critical error: {e}")
        finally:
            # Cleanup
            await self.coinbase_api.close()

async def main():
    """Main entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run integrated server
    server = IntegratedTradingServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())