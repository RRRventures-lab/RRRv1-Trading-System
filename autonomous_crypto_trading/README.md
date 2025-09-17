# Autonomous Crypto Trading Platform

A sophisticated autonomous trading system that uses AI and machine learning to execute cryptocurrency trades with real market data integration.

## Features

- Real-time market data from Coinbase and Polygon APIs
- AI-powered trading decisions using OpenAI
- Machine learning models for market prediction
- Risk management and portfolio optimization
- 30-day paper trading simulation
- Automated deployment to Railway

## Prerequisites

- Python 3.11+
- API keys for:
  - Coinbase (CDP)
  - Polygon
  - OpenAI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RRRventures-lab/trading-platform.git
cd trading-platform
```

2. Create virtual environment:
```bash
python -m venv trading_env
source trading_env/bin/activate  # On Windows: trading_env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Running Locally

```bash
python main.py
```

## Deployment on Railway

The platform is configured for automatic deployment on Railway. Push to the main branch to trigger deployment.

### Environment Variables on Railway

Set the following environment variables in your Railway project:
- `CDP_API_KEY_NAME`
- `CDP_PRIVATE_KEY`
- `POLYGON_API_KEY`
- `OPENAI_API_KEY`

## Project Structure

- `autonomous_system.py` - Core trading system logic
- `main.py` - Entry point for Railway deployment
- `deploy_cloud.py` - Cloud deployment utilities
- `strategies/` - Trading strategy implementations
- `models/` - Machine learning models
- `data/` - Market data storage
- `logs/` - System logs
- `reports/` - Trading reports and analytics

## Safety Features

- Paper trading mode for testing
- Risk management with position limits
- Stop-loss and take-profit mechanisms
- Real-time monitoring and logging
- Automatic failure recovery

## License

Private repository - All rights reserved