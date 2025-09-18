#!/usr/bin/env python3
"""
Full System Launcher
Starts both the trading backend and frontend dashboard
"""

import os
import subprocess
import sys
import asyncio
import signal
import time
from threading import Thread

class FullSystemLauncher:
    """Launches and manages both backend and frontend components"""

    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True

    def start_backend(self):
        """Start the integrated trading server"""
        print("🚀 Starting integrated trading server...")

        try:
            # Set environment variables for ultra-fast mode
            env = os.environ.copy()
            env['ULTRA_FAST_MODE'] = 'true'
            env['PAPER_TRADING'] = 'true'
            env['CYCLE_INTERVAL_MS'] = '100'

            # Activate virtual environment and start the integrated server
            venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_env', 'bin', 'python')
            if not os.path.exists(venv_python):
                venv_python = sys.executable  # Fallback to system python

            self.backend_process = subprocess.Popen([
                venv_python, 'integrated_server.py'
            ], env=env, cwd=os.path.dirname(os.path.abspath(__file__)))

            print("✅ Trading server started")

        except Exception as e:
            print(f"❌ Failed to start backend: {e}")

    def start_frontend(self):
        """Start the Next.js frontend dashboard"""
        print("🎨 Starting frontend dashboard...")

        try:
            dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading-dashboard')

            # Install dependencies if needed
            if not os.path.exists(os.path.join(dashboard_dir, 'node_modules')):
                print("📦 Installing frontend dependencies...")
                subprocess.run(['npm', 'install'], cwd=dashboard_dir, check=True)

            # Start the development server
            self.frontend_process = subprocess.Popen([
                'npm', 'run', 'dev'
            ], cwd=dashboard_dir)

            print("✅ Frontend dashboard started")
            print("📊 Dashboard available at: http://localhost:3000")

        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")

    def stop_all(self):
        """Stop all processes"""
        print("\n🛑 Shutting down all systems...")

        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            print("✅ Backend stopped")

        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            print("✅ Frontend stopped")

        self.running = False
        print("🏁 All systems stopped")

    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n📡 Received signal {signum}")
        self.stop_all()

    def run(self):
        """Run the full system"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        print("🔥 AUTONOMOUS TRADING SYSTEM - FULL DEPLOYMENT 🔥")
        print("=" * 60)
        print("🤖 Multi-Agent Trading System + Live Dashboard")
        print("⚡ Ultra-Fast Mode with Real-Time Visualization")
        print("📊 Coinbase Integration + AI Agent Monitoring")
        print("=" * 60)

        try:
            # Start backend first
            self.start_backend()
            time.sleep(3)  # Give backend time to start

            # Start frontend
            self.start_frontend()
            time.sleep(2)  # Give frontend time to start

            print("\n" + "=" * 60)
            print("🎉 SYSTEM FULLY OPERATIONAL")
            print("=" * 60)
            print("📊 Trading Dashboard: http://localhost:3000")
            print("📡 WebSocket Server:  ws://localhost:8765")
            print("🤖 Backend Status:    Ultra-Fast Multi-Agent Mode")
            print("💰 Starting Capital:  $2,500 (Paper Trading)")
            print("⚡ Trading Frequency: 100ms cycles")
            print("🧠 Active Agents:     9 specialized AI agents")
            print("=" * 60)
            print("\n💡 Press Ctrl+C to stop the system")

            # Keep running and monitor processes
            while self.running:
                time.sleep(1)

                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    print("⚠️  Backend process stopped unexpectedly")
                    break

                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("⚠️  Frontend process stopped unexpectedly")
                    break

        except KeyboardInterrupt:
            print("\n📡 Keyboard interrupt received")
        except Exception as e:
            print(f"\n💥 Error running system: {e}")
        finally:
            self.stop_all()

def main():
    """Main entry point"""
    launcher = FullSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()