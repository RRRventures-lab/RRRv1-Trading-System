# Mem0 AI Integration Guide - RRRv1 Trading System

**Status:** ✅ **INTEGRATED**
**Version:** 1.0.0
**Last Updated:** October 28, 2024

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Setup Instructions](#setup-instructions)
3. [Configuration](#configuration)
4. [API Integration](#api-integration)
5. [Memory Categories](#memory-categories)
6. [Usage Examples](#usage-examples)
7. [Backend Integration](#backend-integration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Mem0?

Mem0 is an AI memory platform that enables applications to remember, learn, and adapt based on past experiences. For RRRv1, this means:

- **Persistent Learning:** Remember past trades and market conditions
- **Strategy Optimization:** Learn which strategies work best in different situations
- **Risk Adaptation:** Adjust risk parameters based on historical losses
- **Market Pattern Recognition:** Identify repeating market patterns
- **Decision Enhancement:** Make better trades based on accumulated knowledge

### Benefits for RRRv1

| Benefit | Description |
|---------|-------------|
| **Adaptive Trading** | Strategies automatically improve based on performance data |
| **Risk Management** | System learns from past liquidation events and adjusts accordingly |
| **Market Intelligence** | Identifies patterns across thousands of trades |
| **Decision Context** | Agents have full historical context for decisions |
| **Continuous Improvement** | System gets smarter every trade |

---

## Setup Instructions

### Step 1: Get Mem0 API Key

1. **Visit Mem0 Platform:**
   - Go to https://app.mem0.ai/
   - Sign up or log in with your account

2. **Create API Key:**
   - Click on Settings (gear icon)
   - Select "API Keys" or "Integrations"
   - Click "Create New API Key"
   - Copy the generated key

3. **Save the Key:**
   - You'll see a key like: `m0-d4EySFOATClbepSX78BI1Rk2WfcWQ1OOtRjRuBPX`
   - Store this securely!

### Step 2: Configure Environment

#### Option A: Environment Variables (Recommended)

```bash
# Add to your shell profile (.zshrc, .bashrc, etc.)
export M0_API_KEY="m0-d4EySFOATClbepSX78BI1Rk2WfcWQ1OOtRjRuBPX"
```

Then reload:
```bash
source ~/.zshrc
```

#### Option B: .env File

```bash
# Copy the example file
cp .env.mem0.example .env.mem0

# Edit and add your API key
nano .env.mem0
# M0_API_KEY=m0-d4EySFOATClbepSX78BI1Rk2WfcWQ1OOtRjRuBPX
```

Load in your Python application:
```python
from dotenv import load_dotenv
load_dotenv('.env.mem0')
```

#### Option C: Direct Configuration

```python
from src.memory import initialize_mem0

mem0_client = initialize_mem0(
    api_key="m0-d4EySFOATClbepSX78BI1Rk2WfcWQ1OOtRjRuBPX"
)
```

### Step 3: Install Dependencies

```bash
# Install Mem0 Python package
pip install mem0ai

# Or update requirements and install all
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Test the integration
python3 -c "from src.memory import get_mem0_client; client = get_mem0_client(); print('✓ Mem0 initialized')"
```

---

## Configuration

### Using .env.mem0

The `.env.mem0.example` file contains all configuration options:

```bash
# Core Settings
M0_API_KEY=your-key-here
MEM0_ENABLED=true
MEM0_LOCAL_FALLBACK=true

# Memory Categories
MEM0_STORE_USER_PREFERENCES=true
MEM0_STORE_MARKET_CONDITIONS=true
MEM0_STORE_STRATEGY_PERFORMANCE=true
MEM0_STORE_RISK_PROFILE=true
MEM0_STORE_PORTFOLIO_PATTERNS=true
MEM0_STORE_LEARNING_INSIGHTS=true

# Retention
MEM0_MAX_TRADE_MEMORIES=1000
MEM0_RETENTION_DAYS=90

# Integration
MEM0_SYNC_INTERVAL=300
MEM0_ENABLE_WEBHOOKS=false
```

### Environment Variable Priority

The system checks for API keys in this order:
1. Direct parameter: `initialize_mem0(api_key="...")`
2. Environment variable: `M0_API_KEY`
3. .env file: `.env.mem0`
4. Fallback: Local storage only

---

## API Integration

### Direct API Usage

#### Option 1: REST API

```python
import requests

# Store a memory
response = requests.post(
    "https://api.mem0.ai/v1/memories",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "content": "BTC showed strong momentum on the 4h chart today",
        "category": "market_conditions"
    }
)

# Recall memories
response = requests.get(
    "https://api.mem0.ai/v1/memories",
    headers={"Authorization": f"Bearer {API_KEY}"},
    params={"category": "market_conditions", "limit": 5}
)
memories = response.json()
```

#### Option 2: Python Wrapper

```python
from mem0 import MemoryClient

client = MemoryClient(api_key="your-key")

# Store
client.add("Market is in uptrend with increasing volume",
           metadata={"type": "market_condition"})

# Recall
memories = client.search("market trends", limit=5)
```

#### Option 3: RRRv1 Integration (Recommended)

```python
from src.memory import get_mem0_client, TradeMemory

# Get the client
client = get_mem0_client()

# Use TradeMemory for trading-specific operations
trade_memory = TradeMemory(client)

# Record a trade
trade_data = {
    "trade_id": "TRD_001",
    "asset": "BTC/USD",
    "action": "BUY",
    "entry_price": 43000,
    "exit_price": 43500,
    "pnl": 250,
    "strategy": "smart_money_strategy",
    "duration_minutes": 45
}

trade_memory.record_trade(trade_data)

# Record market condition
trade_memory.record_market_condition(
    "uptrend",
    "Bitcoin showing strong momentum with higher lows"
)

# Recall and analyze
memories = trade_memory.recall_strategy_performance(asset="BTC/USD")
insights = trade_memory.get_strategy_insights("smart_money_strategy")
```

### Webhook Integration (Optional)

If you want real-time memory updates:

```python
# In your trading agent
app.post("/memory-webhook")
async def handle_memory_webhook(data: dict):
    # Process real-time memory updates
    memory = TradeMemory(get_mem0_client())
    # Update agent based on new memory
```

---

## Memory Categories

### 1. User Preferences
**Purpose:** Store user trading preferences and settings

**Example:**
```python
client.store(
    "user_preferences",
    "User prefers spot trading with maximum 2x leverage",
    metadata={"leverage": 2, "style": "conservative"}
)
```

**Use Cases:**
- Risk tolerance levels
- Preferred trading pairs
- Trading schedule preferences
- Alert thresholds

### 2. Market Conditions
**Purpose:** Store observations about market conditions

**Example:**
```python
trade_memory.record_market_condition(
    "consolidation",
    "BTC consolidating between $43k and $44k for 48 hours with decreasing volume"
)
```

**Use Cases:**
- Trend analysis
- Support/resistance levels
- Volatility observations
- Market regime identification

### 3. Strategy Performance
**Purpose:** Track how each strategy performs

**Example:**
```python
trade_memory.record_trade({
    "asset": "ETH/USD",
    "action": "BUY",
    "strategy": "smart_money_strategy",
    "pnl": 150,
    "duration_minutes": 30
})
```

**Use Cases:**
- Win/loss tracking per strategy
- Performance in different market conditions
- Optimal position sizes
- Entry/exit pattern analysis

### 4. Risk Profile
**Purpose:** Document risk management lessons

**Example:**
```python
trade_memory.record_risk_event(
    "liquidation_warning",
    "Position BTC_SHORT hit 20% liquidation distance during flash crash",
    "Reduced position size by 30% to prevent future liquidations"
)
```

**Use Cases:**
- Liquidation events
- Drawdown patterns
- Correlation breakdowns
- Lesson learned documentation

### 5. Portfolio Patterns
**Purpose:** Identify portfolio-level patterns

**Example:**
```python
client.store(
    "portfolio_patterns",
    "Portfolio tends to drawdown 5-8% before major recoveries",
    metadata={"pattern_type": "drawdown", "duration_days": 3}
)
```

**Use Cases:**
- Asset allocation patterns
- Diversification opportunities
- Rebalancing triggers
- Correlation observations

### 6. Learning Insights
**Purpose:** Store high-level insights and conclusions

**Example:**
```python
client.store(
    "learning_insights",
    "Smart Money strategy outperforms in trending markets by 3x",
    metadata={"confidence": 0.85, "sample_size": 100}
)
```

**Use Cases:**
- Insights summary
- General observations
- Decision rules
- Best practices documentation

---

## Usage Examples

### Example 1: Record Trade After Execution

```python
from src.memory import TradeMemory, get_mem0_client

def record_trade_to_memory(trade_result: dict):
    """Record executed trade to Mem0"""

    memory = TradeMemory(get_mem0_client())

    trade_data = {
        "trade_id": trade_result["id"],
        "asset": trade_result["symbol"],
        "action": trade_result["side"],
        "entry_price": trade_result["entry"],
        "exit_price": trade_result["exit"],
        "pnl": trade_result["profit_loss"],
        "strategy": trade_result["strategy_name"],
        "duration_minutes": trade_result["duration"]
    }

    success = memory.record_trade(trade_data)

    if success:
        print(f"✓ Trade {trade_data['trade_id']} recorded to Mem0")
    else:
        print(f"✗ Failed to record trade to Mem0")

# Usage
trade_result = {
    "id": "TRD_12345",
    "symbol": "BTC/USD",
    "side": "BUY",
    "entry": 43000,
    "exit": 43500,
    "profit_loss": 250,
    "strategy_name": "smart_money_strategy",
    "duration": 45
}

record_trade_to_memory(trade_result)
```

### Example 2: Recall Performance Data for Strategy Analysis

```python
def analyze_strategy_performance(strategy_name: str):
    """Analyze strategy performance from memories"""

    memory = TradeMemory(get_mem0_client())

    # Get last 20 trades for this strategy
    memories = memory.recall_strategy_performance(limit=20)

    # Analyze results
    total_trades = len(memories)
    winning = sum(1 for m in memories if "P&L: $" in str(m))
    win_rate = (winning / total_trades * 100) if total_trades > 0 else 0

    print(f"""
    Strategy: {strategy_name}
    Total Trades: {total_trades}
    Winning Trades: {winning}
    Win Rate: {win_rate:.1f}%
    """)

    # Get insights
    insights = memory.get_strategy_insights(strategy_name)
    print(f"Insights:\n{insights}")

# Usage
analyze_strategy_performance("smart_money_strategy")
```

### Example 3: Learn from Risk Events

```python
def handle_risk_event(event_type: str, description: str):
    """Record and learn from risk events"""

    memory = TradeMemory(get_mem0_client())

    # Determine appropriate response
    if event_type == "liquidation_warning":
        impact = "High - Immediate position reduction needed"
    elif event_type == "drawdown":
        impact = "Medium - Monitor additional positions"
    else:
        impact = "Low - Log for analysis"

    # Record event
    memory.record_risk_event(
        event_type=event_type,
        description=description,
        impact=impact
    )

    # Recall similar events
    risk_memories = memory.mem0.recall(
        "risk_profile",
        limit=10
    )

    print(f"Event recorded. Found {len(risk_memories)} similar events in history")

# Usage
handle_risk_event(
    "liquidation_warning",
    "Position BTC_LONG approaching 15% liquidation distance"
)
```

---

## Backend Integration

### FastAPI Endpoint for Memory Operations

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.memory import TradeMemory, get_mem0_client

app = FastAPI()

class TradeRecordRequest(BaseModel):
    trade_id: str
    asset: str
    action: str
    entry_price: float
    exit_price: float
    pnl: float
    strategy: str
    duration_minutes: int

@app.post("/api/memory/record-trade")
async def record_trade_endpoint(request: TradeRecordRequest):
    """API endpoint to record a trade in Mem0"""

    try:
        memory = TradeMemory(get_mem0_client())

        success = memory.record_trade(request.dict())

        if success:
            return {
                "status": "success",
                "message": f"Trade {request.trade_id} recorded"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to record trade")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/strategy-performance/{strategy_name}")
async def get_strategy_performance(strategy_name: str):
    """Get strategy performance from memories"""

    try:
        memory = TradeMemory(get_mem0_client())

        memories = memory.recall_strategy_performance(limit=20)
        insights = memory.get_strategy_insights(strategy_name)

        return {
            "strategy": strategy_name,
            "memories": memories,
            "insights": insights
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/record-risk-event")
async def record_risk_event(
    event_type: str,
    description: str,
    impact: str
):
    """Record a risk event in Mem0"""

    try:
        memory = TradeMemory(get_mem0_client())

        success = memory.record_risk_event(
            event_type=event_type,
            description=description,
            impact=impact
        )

        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record event")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Integrating with Trading Agent

```python
from src.agents.trading_agent import TradingAgent
from src.memory import TradeMemory, get_mem0_client

class EnhancedTradingAgent(TradingAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = TradeMemory(get_mem0_client())

    async def execute_trade(self, signal: TradeSignal):
        """Execute trade and record to memory"""

        # Execute the trade normally
        execution = await super().execute_trade(signal)

        # After trade closes, record to memory
        if execution.status == "closed":
            self.memory.record_trade({
                "trade_id": execution.trade_id,
                "asset": execution.asset,
                "action": execution.action,
                "entry_price": execution.entry_price,
                "exit_price": execution.exit_price or 0,
                "pnl": execution.pnl or 0,
                "strategy": signal.strategy,
                "duration_minutes": execution.duration
            })

        return execution

    def get_strategy_insights(self, strategy_name: str):
        """Get learned insights about a strategy"""
        return self.memory.get_strategy_insights(strategy_name)
```

---

## Troubleshooting

### Problem: "M0_API_KEY not found"

**Error:**
```
⚠ Mem0 API key not found. Set M0_API_KEY environment variable.
```

**Solution:**
1. Check if API key is set: `echo $M0_API_KEY`
2. If empty, add to shell profile:
   ```bash
   export M0_API_KEY="m0-d4EySFOATClbepSX78BI1Rk2WfcWQ1OOtRjRuBPX"
   source ~/.zshrc
   ```
3. Or use environment file:
   ```bash
   python3 -c "import os; os.getenv('M0_API_KEY'); print(os.getenv('M0_API_KEY'))"
   ```

### Problem: "Failed to store memory"

**Error:**
```
✗ Memory stored: user_preferences
✗ Failed to store memory: Connection refused
```

**Solution:**
1. Verify API key is valid: Check at https://app.mem0.ai/settings
2. Check network connectivity: `curl https://api.mem0.ai/v1/health`
3. Enable local fallback (default):
   ```python
   client = Mem0Client(api_key="...")
   # System will automatically use local storage if API fails
   ```

### Problem: "Cannot import mem0ai"

**Error:**
```
ModuleNotFoundError: No module named 'mem0'
```

**Solution:**
1. Install the package:
   ```bash
   pip install mem0ai
   ```
2. Or update all requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Verify installation:
   ```bash
   python3 -c "import mem0; print(mem0.__version__)"
   ```

### Problem: "Memory operations are slow"

**Solution:**
1. Check API key validity and rate limits
2. Increase `MEM0_SYNC_INTERVAL` to reduce update frequency
3. Enable local caching:
   ```python
   MEM0_LOCAL_FALLBACK=true
   ```
4. Batch operations:
   ```python
   # Instead of many small calls
   memories = []
   for trade in trades:
       memories.append(format_trade(trade))

   # Store all at once
   for memory in memories:
       client.store(memory.category, memory.content)
   ```

### Problem: "Local storage file not found"

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: './data/memory/
```

**Solution:**
1. Create the directory:
   ```bash
   mkdir -p ./data/memory/
   chmod 755 ./data/memory/
   ```
2. Or disable local storage:
   ```python
   MEM0_LOCAL_FALLBACK=false
   ```

---

## Best Practices

### 1. Use Structured Metadata

```python
# Good: Clear, queryable metadata
memory.store(
    "strategy_performance",
    content,
    metadata={
        "strategy": "smart_money",
        "asset": "BTC/USD",
        "win": True,
        "pnl": 250,
        "date": "2024-10-28"
    }
)

# Avoid: Unstructured metadata
memory.store("strategy_performance", content)
```

### 2. Regular Memory Cleanup

```python
# Archive old memories periodically
old_memories = client.recall("strategy_performance", limit=1000)
for memory in old_memories:
    if memory["timestamp"] < cutoff_date:
        client.delete(memory["id"])
```

### 3. Monitor Memory Growth

```python
# Track memory usage
memory_stats = {
    "total_trades": len(client.memories["strategy_performance"]),
    "market_conditions": len(client.memories["market_conditions"]),
    "risk_events": len(client.memories["risk_profile"])
}

logger.info(f"Memory stats: {memory_stats}")
```

### 4. Use TradeMemory Class

```python
# Better: Use provided TradeMemory class
from src.memory import TradeMemory, get_mem0_client

memory = TradeMemory(get_mem0_client())
memory.record_trade(trade_data)

# Instead of:
client.store("strategy_performance", ...)
```

---

## Next Steps

1. ✅ Set up Mem0 API key
2. ✅ Configure environment variables
3. ✅ Install dependencies
4. ✅ Test integration with example script
5. Integrate memory recording in trading agent
6. Add memory recall to decision-making
7. Set up automated analysis of memories
8. Monitor memory growth and performance

---

## Additional Resources

- **Mem0 Documentation:** https://docs.mem0.ai/
- **API Reference:** https://api.mem0.ai/docs
- **Getting Started:** https://app.mem0.ai/
- **Support:** support@mem0.ai

---

## Summary

Mem0 integration provides RRRv1 with persistent learning capabilities:

| Feature | Benefit |
|---------|---------|
| **API Integration** | Easy cloud storage of memories |
| **6 Memory Categories** | Comprehensive memory structure |
| **TradeMemory Class** | Simple trading-specific interface |
| **Local Fallback** | Works offline if API unavailable |
| **BackendIntegration** | FastAPI endpoints for all operations |
| **Full Logging** | Track all memory operations |

**Status:** ✅ Ready for Production Use

---

**Generated:** October 28, 2024
**Version:** 1.0.0
**Author:** RRRv1 Development Team
