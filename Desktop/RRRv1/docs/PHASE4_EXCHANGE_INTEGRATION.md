# Phase 4: Real Exchange Integration

**Status:** ✅ **COMPLETE**
**Date:** October 28, 2024
**Components:** Hyperliquid API + Coinbase API + Unified Integration Layer

---

## Overview

Phase 4 implements direct integration with real trading exchanges, enabling live order execution, position management, and market data feeds. The system now connects to Hyperliquid (primary) and Coinbase (secondary) with automatic allocation management.

### What Was Implemented

1. **Hyperliquid API Client** - Full REST API integration
2. **Coinbase API Client** - Advanced Trade API integration
3. **Unified Exchange Layer** - Multi-exchange coordination
4. **Order Execution** - Real trade placement and management
5. **Position Synchronization** - Live position tracking
6. **Allocation Management** - 80/20 split enforcement

---

## Architecture

### Components

#### 1. Hyperliquid API Client (`backend/hyperliquid_api.py`)

Full Hyperliquid exchange integration (600+ lines):

**Features:**
- HMAC-SHA256 authentication
- Async HTTP communication with aiohttp
- Connection pooling and session management
- Comprehensive error handling
- Request timeout configuration

**Supported Operations:**

*Account Management:*
- `get_account_info()` - Account details
- `get_balance()` - Current balance

*Position Operations:*
- `get_open_positions()` - All open positions
- `get_position(asset)` - Specific position
- `close_position(asset)` - Close position
- `reduce_position(asset, amount)` - Reduce size

*Order Management:*
- `place_order()` - Place new order (MARKET/LIMIT/STOP)
- `cancel_order(order_id)` - Cancel order
- `get_open_orders()` - List open orders

*Market Data:*
- `get_market_prices()` - All prices
- `get_price(asset)` - Single price
- `get_orderbook(asset)` - Orderbook data

**Key Classes:**
- `HyperliquidOrder` - Order representation
- `HyperliquidPosition` - Position representation
- `HyperliquidBalance` - Balance information
- `OrderType` - MARKET, LIMIT, STOP_MARKET, etc.
- `OrderStatus` - OPEN, FILLED, CANCELLED, etc.

**Authentication:**
```python
client = HyperliquidAPIClient(api_key, api_secret, testnet=False)
await client.connect()
# Use client methods
await client.disconnect()
```

#### 2. Coinbase API Client (`backend/coinbase_api.py`)

Coinbase Advanced Trade API integration (500+ lines):

**Features:**
- HMAC-SHA256 signature generation
- REST API communication with aiohttp
- Support for spot and margin trading
- Comprehensive order management
- Market data access

**Supported Operations:**

*Account Management:*
- `get_account_info()` - Account details
- `get_balance()` - Account balance

*Position Operations (Margin):*
- `get_open_positions()` - All margin positions
- `get_position(product_id)` - Specific position
- `close_position(product_id)` - Close position
- `reduce_position(product_id, amount)` - Reduce size

*Order Management:*
- `place_order()` - Place order (MARKET/LIMIT/STOP)
- `cancel_order(order_id)` - Cancel order
- `get_open_orders()` - List open orders

*Market Data:*
- `get_product(product_id)` - Product info
- `get_price(product_id)` - Current price
- `get_orderbook(product_id)` - Orderbook

**Key Classes:**
- `CoinbaseOrder` - Order representation
- `CoinbasePosition` - Position representation
- `CoinbaseBalance` - Balance information
- `OrderType` - MARKET, LIMIT, STOP
- `OrderStatus` - PENDING, OPEN, FILLED, etc.

**Authentication:**
```python
client = CoinbaseAPIClient(api_key, api_secret)
await client.connect()
# Use client methods
await client.disconnect()
```

#### 3. Unified Exchange Layer (`backend/exchange_integration.py`)

Multi-exchange coordination (600+ lines):

**Features:**
- Single interface for both exchanges
- Automatic exchange selection based on allocation
- Unified order execution
- Allocation tracking and enforcement
- Health checks across venues

**Key Methods:**

*Health & Status:*
- `health_check()` - Check both exchanges
- `get_allocation_status()` - Current 80/20 allocation

*Account Management:*
- `get_balances()` - Balances from both exchanges
- `get_all_positions()` - Positions from both venues

*Order Execution:*
- `place_order()` - Place on selected exchange
- `close_position()` - Close on correct exchange
- `reduce_position()` - Reduce on correct exchange

*Position Management:*
- `get_position(asset)` - Find position anywhere
- Auto-select correct exchange for operations

*Market Data:*
- `get_price(asset)` - Price from primary exchange
- `get_prices(assets)` - Multiple prices

**Integration Example:**
```python
client = UnifiedExchangeClient(
    hl_key=hl_api_key,
    hl_secret=hl_api_secret,
    cb_key=cb_api_key,
    cb_secret=cb_api_secret
)

await client.connect()

# Place order (auto-selects exchange)
result = await client.place_order(
    asset="BTC",
    side="BUY",
    size=0.5,
    leverage=5.0
)

# Get allocation status
status = await client.get_allocation_status()
# {
#     "hyperliquid": {"target": 0.80, "actual": 0.78, ...},
#     "coinbase": {"target": 0.20, "actual": 0.22, ...}
# }

await client.disconnect()
```

---

## API Methods Reference

### Hyperliquid API

```python
# Account
await client.get_account_info() → Dict
await client.get_balance() → HyperliquidBalance

# Positions
await client.get_open_positions() → List[HyperliquidPosition]
await client.get_position(asset: str) → Optional[HyperliquidPosition]
await client.close_position(asset: str) → Optional[HyperliquidOrder]
await client.reduce_position(asset: str, amount: float) → Optional[HyperliquidOrder]

# Orders
await client.place_order(
    asset: str,
    side: OrderSide,
    size: float,
    order_type: OrderType = OrderType.MARKET,
    price: Optional[float] = None,
    leverage: float = 1.0,
    reduce_only: bool = False
) → HyperliquidOrder

await client.cancel_order(order_id: str) → bool
await client.get_open_orders(asset: Optional[str] = None) → List[HyperliquidOrder]

# Market Data
await client.get_market_prices() → Dict[str, float]
await client.get_price(asset: str) → Optional[float]
await client.get_orderbook(asset: str, depth: int = 20) → Dict

# Health
await client.health_check() → bool
```

### Coinbase API

```python
# Account
await client.get_account_info() → Dict
await client.get_balance() → CoinbaseBalance

# Positions
await client.get_open_positions() → List[CoinbasePosition]
await client.get_position(product_id: str) → Optional[CoinbasePosition]
await client.close_position(product_id: str) → Optional[CoinbaseOrder]
await client.reduce_position(product_id: str, amount: float) → Optional[CoinbaseOrder]

# Orders
await client.place_order(
    product_id: str,
    side: OrderSide,
    order_type: OrderType,
    size: Optional[float] = None,
    price: Optional[float] = None,
    post_only: bool = False
) → CoinbaseOrder

await client.cancel_order(order_id: str) → bool
await client.get_open_orders(product_id: Optional[str] = None) → List[CoinbaseOrder]

# Market Data
await client.get_product(product_id: str) → Dict
await client.get_price(product_id: str) → Optional[float]
await client.get_orderbook(product_id: str, level: int = 1) → Dict

# Health
await client.health_check() → bool
```

### Unified Exchange Client

```python
# Connection
await client.connect() → None
await client.disconnect() → None

# Health & Status
await client.health_check() → Dict[str, bool]
await client.get_allocation_status() → Dict

# Account
await client.get_balances() → Dict[str, Dict]

# Positions
await client.get_all_positions() → Dict[str, List]
await client.get_position(asset: str) → Optional[Dict]
await client.close_position(asset: str) → ExecutionResult
await client.reduce_position(asset: str, amount: float) → ExecutionResult

# Orders (auto-selects exchange based on allocation)
await client.place_order(
    asset: str,
    side: str,
    size: float,
    exchange: Optional[ExchangeType] = None,
    price: Optional[float] = None,
    leverage: float = 1.0
) → ExecutionResult

# Market Data
await client.get_price(asset: str) → Optional[float]
await client.get_prices(assets: List[str]) → Dict[str, float]
```

---

## Setup & Configuration

### Prerequisites

1. **API Credentials**
   - Hyperliquid API key and secret
   - Coinbase API key and secret

2. **Python Packages**
   ```bash
   pip install aiohttp
   ```

3. **Environment Variables**
   ```bash
   export HYPERLIQUID_KEY="your-hl-key"
   export HYPERLIQUID_SECRET="your-hl-secret"
   export HYPERLIQUID_TESTNET="false"  # or "true" for testnet

   export COINBASE_KEY="your-cb-key"
   export COINBASE_SECRET="your-cb-secret"
   ```

### Getting API Credentials

**Hyperliquid:**
1. Go to https://hyperliquid.xyz
2. Create account
3. Generate API key in settings
4. Copy key and secret

**Coinbase:**
1. Go to https://coinbase.com
2. Create account
3. Go to Settings → API
4. Create API key with Advanced Trade permissions
5. Copy key and secret

### Testing Setup

**Use Hyperliquid Testnet:**
```python
client = HyperliquidAPIClient(
    api_key=hl_key,
    api_secret=hl_secret,
    testnet=True  # Use testnet, not mainnet
)
```

---

## Usage Examples

### JavaScript/Node.js

```javascript
// Note: JavaScript integration example (for frontend)
const UNIFIED_API = "http://localhost:8000";
const API_KEY = "rrr-your-key";

// Place order via unified endpoint
async function placeOrder(asset, side, size, leverage = 1.0) {
  const response = await fetch(`${UNIFIED_API}/api/exchange/order`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      asset,
      side,
      size,
      leverage
    })
  });

  return await response.json();
}

// Get positions from both exchanges
async function getAllPositions() {
  const response = await fetch(
    `${UNIFIED_API}/api/exchange/positions`,
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );

  return await response.json();
}

// Get allocation status
async function getAllocationStatus() {
  const response = await fetch(
    `${UNIFIED_API}/api/exchange/allocation`,
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );

  return await response.json();
}
```

### Python

```python
import asyncio
from exchange_integration import UnifiedExchangeClient, ExchangeType

async def main():
    client = UnifiedExchangeClient(
        hl_key="your-hl-key",
        hl_secret="your-hl-secret",
        cb_key="your-cb-key",
        cb_secret="your-cb-secret"
    )

    await client.connect()

    try:
        # Check health
        health = await client.health_check()
        print(f"Health: {health}")

        # Get balances
        balances = await client.get_balances()
        print(f"Balances: {balances}")

        # Get positions
        positions = await client.get_all_positions()
        print(f"Positions: {positions}")

        # Get allocation
        allocation = await client.get_allocation_status()
        print(f"Allocation: {allocation}")

        # Place order (auto-selects exchange)
        result = await client.place_order(
            asset="BTC",
            side="BUY",
            size=0.1,
            leverage=5.0
        )
        print(f"Order result: {result}")

        # Close position
        close_result = await client.close_position("BTC")
        print(f"Close result: {close_result}")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Allocation Management

### 80/20 Split Strategy

The system automatically maintains:
- **80% Hyperliquid** - Primary venue for leveraged trading
- **20% Coinbase** - Secondary venue for conservative positions

### Auto-Selection Logic

When placing an order without specifying an exchange:

```
Current Allocation: HL=75%, CB=25%
Target Allocation:   HL=80%, CB=20%

HL below target? YES → Use Hyperliquid
CB above target? YES → Consider Coinbase

Result: Use Hyperliquid to rebalance toward target
```

### Checking Allocation

```python
status = await client.get_allocation_status()
# {
#     "hyperliquid": {
#         "target": 0.80,
#         "actual": 0.78,           # 2% below target
#         "drift": 0.02,
#         "notional_value": 78000
#     },
#     "coinbase": {
#         "target": 0.20,
#         "actual": 0.22,           # 2% above target
#         "drift": 0.02,
#         "notional_value": 22000
#     },
#     "total_notional": 100000
# }
```

### Rebalancing

Triggered when drift exceeds threshold (typically 5%):

```python
# Drift detected: HL=70%, CB=30% (target 80/20)
# Action: Reduce Coinbase positions, increase Hyperliquid
```

---

## Error Handling

### Network Errors

```python
try:
    await client.place_order(...)
except asyncio.TimeoutError:
    print("API request timeout")
except Exception as e:
    print(f"API error: {e}")
```

### Order Failures

```python
result = await client.place_order(...)

if not result.success:
    print(f"Order failed: {result.message}")
    print(f"Error status: {result.status}")
```

### Position Not Found

```python
position = await client.get_position("BTC")

if not position:
    print("No position found for BTC")
else:
    print(f"Position: {position}")
```

---

## Testing

### Unit Tests

```python
import pytest
from hyperliquid_api import HyperliquidAPIClient, OrderSide, OrderType

@pytest.mark.asyncio
async def test_get_balance():
    client = HyperliquidAPIClient(api_key, api_secret, testnet=True)
    await client.connect()

    balance = await client.get_balance()
    assert balance.total_balance > 0

    await client.disconnect()

@pytest.mark.asyncio
async def test_place_order():
    client = HyperliquidAPIClient(api_key, api_secret, testnet=True)
    await client.connect()

    order = await client.place_order(
        asset="BTC",
        side=OrderSide.BUY,
        size=0.1,
        order_type=OrderType.MARKET
    )
    assert order.order_id is not None

    await client.disconnect()
```

### Integration Tests

```bash
# Test Hyperliquid connection
python3 << 'EOF'
import asyncio
from hyperliquid_api import HyperliquidAPIClient

async def test():
    client = HyperliquidAPIClient(api_key, api_secret, testnet=True)
    await client.connect()

    # Test health check
    healthy = await client.health_check()
    assert healthy, "API not healthy"

    # Test get balance
    balance = await client.get_balance()
    print(f"Balance: {balance.total_balance}")

    # Test get prices
    prices = await client.get_market_prices()
    print(f"Got prices for {len(prices)} assets")

    await client.disconnect()
    print("All tests passed!")

asyncio.run(test())
EOF
```

---

## Common Issues & Solutions

### Issue: "Authentication failed"

**Cause:** Invalid API key or secret

**Solution:**
1. Verify credentials in environment variables
2. Check key hasn't been revoked
3. Generate new key if needed
4. Ensure no whitespace in key/secret

### Issue: "API request timeout"

**Cause:** Network latency or API overload

**Solution:**
```python
# Increase timeout
client = HyperliquidAPIClient(
    api_key, api_secret,
    request_timeout=30.0  # 30 seconds
)
```

### Issue: "Insufficient balance"

**Cause:** Not enough available balance for order

**Solution:**
1. Check balance: `await client.get_balance()`
2. Reduce order size
3. Close some positions
4. Deposit more funds

### Issue: "Position not found"

**Cause:** Position closed or doesn't exist on specified exchange

**Solution:**
1. Check all positions: `await client.get_all_positions()`
2. Verify asset name (e.g., "BTC" vs "BTC-USD")
3. Ensure position is on correct exchange

### Issue: "Order placement failed"

**Cause:** Market conditions, leverage issues, or API problems

**Solution:**
1. Check order parameters (size, price, leverage)
2. Verify market is open
3. Check API logs for details
4. Retry with different parameters

---

## Monitoring & Observability

### Health Monitoring

```python
# Check exchange health
health = await client.health_check()
if not health["all_operational"]:
    print("Warning: One or more exchanges down")
```

### Position Monitoring

```python
# Get all positions
positions = await client.get_all_positions()

print(f"Total positions: {positions['total_count']}")
print(f"Hyperliquid: {len(positions['hyperliquid'])} positions")
print(f"Coinbase: {len(positions['coinbase'])} positions")
```

### Allocation Monitoring

```python
# Check allocation
status = await client.get_allocation_status()

hl_drift = status["hyperliquid"]["drift"]
cb_drift = status["coinbase"]["drift"]

if hl_drift > 0.05:
    print(f"Warning: HL allocation drift: {hl_drift:.1%}")
if cb_drift > 0.05:
    print(f"Warning: CB allocation drift: {cb_drift:.1%}")
```

---

## Performance Considerations

### Connection Pooling

Both clients use aiohttp connection pooling for efficiency:
```python
# Single session reused for all requests
# Automatic connection management
await client.connect()
# ... use client ...
await client.disconnect()
```

### Request Rate Limiting

- **Hyperliquid:** 10 requests/second (rate limiter applied)
- **Coinbase:** 5 requests/second (rate limiter applied)

Respect these limits in production.

### Async/Await Pattern

All network calls are async:
```python
# Parallel requests for efficiency
positions = await client.get_all_positions()
prices = await client.get_market_prices()
balance = await client.get_balance()
# All happen concurrently, not sequentially
```

---

## Integration with RRRv1 System

### Adding to API Server

```python
# In backend/api_server.py

from exchange_integration import UnifiedExchangeClient

# Initialize
exchange_client = UnifiedExchangeClient(
    hl_key=os.getenv("HYPERLIQUID_KEY"),
    hl_secret=os.getenv("HYPERLIQUID_SECRET"),
    cb_key=os.getenv("COINBASE_KEY"),
    cb_secret=os.getenv("COINBASE_SECRET")
)

# New endpoints
@app.get("/api/exchange/balance")
async def get_exchange_balance(api_key: str = Depends(check_rate_limit)):
    return await exchange_client.get_balances()

@app.get("/api/exchange/positions")
async def get_exchange_positions(api_key: str = Depends(check_rate_limit)):
    return await exchange_client.get_all_positions()

@app.get("/api/exchange/allocation")
async def get_exchange_allocation(api_key: str = Depends(check_rate_limit)):
    return await exchange_client.get_allocation_status()

@app.post("/api/exchange/order")
async def place_exchange_order(
    asset: str,
    side: str,
    size: float,
    api_key: str = Depends(check_rate_limit)
):
    return await exchange_client.place_order(asset, side, size)
```

### With Trading Agent

```python
# In trading agent
from exchange_integration import UnifiedExchangeClient

class TradingAgent:
    def __init__(self):
        self.exchange = UnifiedExchangeClient(...)

    async def execute_trade(self, asset, side, size):
        result = await self.exchange.place_order(asset, side, size)
        return result

    async def close_position(self, asset):
        return await self.exchange.close_position(asset)
```

---

## Next Steps

### Your Action Items

1. ✅ **Add API credentials** (5 minutes)
   ```bash
   export HYPERLIQUID_KEY="your-key"
   export HYPERLIQUID_SECRET="your-secret"
   export COINBASE_KEY="your-key"
   export COINBASE_SECRET="your-secret"
   ```

2. ✅ **Test on testnet** (10 minutes)
   ```bash
   python3 << 'EOF'
   # Test script here
   EOF
   ```

3. ✅ **Check health** (2 minutes)
   ```python
   health = await client.health_check()
   ```

4. ✅ **Get balances** (2 minutes)
   ```python
   balances = await client.get_balances()
   ```

5. ✅ **Place test order** (5 minutes)
   ```python
   # On testnet first!
   result = await client.place_order(...)
   ```

---

## Summary

**Phase 4 Achievements:**
- ✅ Hyperliquid API client (600+ lines)
- ✅ Coinbase API client (500+ lines)
- ✅ Unified exchange layer (600+ lines)
- ✅ Multi-exchange order execution
- ✅ Position synchronization
- ✅ Allocation management (80/20)
- ✅ Health checks and monitoring

**Result:**
- **Direct exchange connectivity**
- **Live order execution**
- **Real-time position tracking**
- **Automatic allocation management**

---

**Generated:** October 28, 2024
**Status:** ✅ Ready for Integration
