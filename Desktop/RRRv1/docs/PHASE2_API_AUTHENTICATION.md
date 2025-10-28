# Phase 2: API Authentication & Rate Limiting

**Status:** ✅ **COMPLETE**
**Date:** October 28, 2024
**Components:** API Key Management + Rate Limiting

---

## Overview

Phase 2 implements single-user API key authentication and rate limiting for the RRRv1 trading dashboard. This prevents unauthorized access and protects the system from abuse.

### What Was Implemented

1. **API Key Authentication** - Secure header-based authentication
2. **Rate Limiting** - Request throttling (100 req/min, 10000 req/hour)
3. **Key Management Endpoints** - Create, list, and revoke API keys
4. **WebSocket Security** - Protected real-time connections
5. **CORS Configuration** - Restricted to localhost by default
6. **Comprehensive Logging** - Track all authentication events

---

## Architecture

### Authentication Flow

```
Client Request
    ↓
Header: X-API-Key: rrr-xxxxx
    ↓
verify_api_key() dependency
    ↓
check_rate_limit() dependency
    ↓
Endpoint Handler
```

### Key Storage

- **Format:** SHA-256 hashed (never plaintext)
- **Location:** `config/api_keys.json`
- **Permissions:** 0o600 (owner read/write only)
- **Metadata:** created_at, last_used, request_count, enabled status

### Rate Limiting

- **Per-minute limit:** 100 requests
- **Per-hour limit:** 10,000 requests
- **Tracking:** Per API key in memory
- **Headers:** Returns `Retry-After` on 429 status

---

## API Key Management

### Generate API Key

**Endpoint:** `POST /api/auth/keys`

**Requirements:** Valid API key in `X-API-Key` header

**Request:**
```bash
curl -X POST \
  -H "X-API-Key: rrr-existing-key" \
  -H "Content-Type: application/json" \
  "http://localhost:8000/api/auth/keys?name=my_key"
```

**Response:**
```json
{
  "status": "success",
  "message": "New API key generated. Save this securely - it won't be shown again!",
  "api_key": "rrr-a1b2c3d4e5f6...",
  "name": "my_key",
  "usage": "Use in request header: X-API-Key: rrr-a1b2c3d4e5f6..."
}
```

**Important:** Save the API key immediately. It will not be shown again!

### List API Keys

**Endpoint:** `GET /api/auth/keys`

**Requirements:** Valid API key

**Request:**
```bash
curl -H "X-API-Key: rrr-your-key" \
  "http://localhost:8000/api/auth/keys"
```

**Response:**
```json
{
  "keys": [
    {
      "name": "default",
      "created_at": "2024-10-28T12:00:00.000000",
      "last_used": "2024-10-28T14:30:00.000000",
      "enabled": true,
      "request_count": 150
    },
    {
      "name": "my_key",
      "created_at": "2024-10-28T14:25:00.000000",
      "last_used": null,
      "enabled": true,
      "request_count": 0
    }
  ],
  "stats": {
    "total_keys": 2,
    "enabled_keys": 2,
    "disabled_keys": 0,
    "total_requests": 150
  }
}
```

### Revoke API Key

**Endpoint:** `POST /api/auth/keys/{key_name}/revoke`

**Requirements:** Valid API key

**Request:**
```bash
curl -X POST \
  -H "X-API-Key: rrr-your-key" \
  "http://localhost:8000/api/auth/keys/old_key/revoke"
```

**Response:**
```json
{
  "status": "success",
  "message": "API key 'old_key' has been revoked"
}
```

### Check Authentication Status

**Endpoint:** `GET /api/auth/status`

**Request:**
```bash
curl -H "X-API-Key: rrr-your-key" \
  "http://localhost:8000/api/auth/status"
```

**Response:**
```json
{
  "authenticated": true,
  "key_valid": true,
  "rate_limit_status": {
    "requests_this_minute": 5,
    "requests_this_hour": 42,
    "limit_minute": 100,
    "limit_hour": 10000,
    "minute_remaining": 95,
    "hour_remaining": 9958
  },
  "keys_configured": 2
}
```

### Get Rate Limit Usage

**Endpoint:** `GET /api/auth/usage`

**Request:**
```bash
curl -H "X-API-Key: rrr-your-key" \
  "http://localhost:8000/api/auth/usage"
```

**Response:**
```json
{
  "current_usage": {
    "requests_this_minute": 5,
    "requests_this_hour": 42,
    "limit_minute": 100,
    "limit_hour": 10000,
    "minute_remaining": 95,
    "hour_remaining": 9958
  },
  "time_checked": "2024-10-28T14:30:45.123456"
}
```

---

## Protected Endpoints

All data endpoints now require `X-API-Key` header:

### Data Endpoints (GET)
- `GET /api/portfolio` - Portfolio status
- `GET /api/positions` - Active positions
- `GET /api/strategies` - Strategy performance
- `GET /api/metrics` - Trading metrics
- `GET /api/funding` - Funding arbitrage stats
- `GET /api/trades?limit=50` - Trade history
- `GET /api/dashboard` - Complete dashboard state

### Control Endpoints (POST)
- `POST /api/emergency-stop` - Emergency stop
- `POST /api/close-position/{asset}` - Close position
- `POST /api/reduce-position/{asset}?reduction_pct=0.5` - Reduce position

### WebSocket Endpoint
- `ws://localhost:8000/ws/live?api_key=YOUR_KEY` - Real-time updates

---

## Usage Examples

### JavaScript/Node.js

```javascript
const API_KEY = "rrr-your-key-here";

// REST API call
async function getPortfolio() {
  const response = await fetch("http://localhost:8000/api/portfolio", {
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    }
  });

  if (response.status === 401) {
    console.error("Invalid API key");
    return;
  }

  if (response.status === 429) {
    console.error("Rate limit exceeded");
    return;
  }

  return await response.json();
}

// WebSocket connection
function connectWebSocket() {
  const ws = new WebSocket(`ws://localhost:8000/ws/live?api_key=${API_KEY}`);

  ws.onopen = () => console.log("Connected");
  ws.onerror = (event) => {
    if (event.code === 4001) {
      console.error("Invalid API key for WebSocket");
    } else if (event.code === 4029) {
      console.error("Rate limit exceeded on WebSocket");
    }
  };

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log("Received update:", update);
  };

  return ws;
}
```

### Python

```python
import requests
import websocket
import json

API_KEY = "rrr-your-key-here"
BASE_URL = "http://localhost:8000"

# REST API call
def get_portfolio():
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/api/portfolio", headers=headers)

    if response.status_code == 401:
        print("Invalid API key")
        return None

    if response.status_code == 429:
        print("Rate limit exceeded")
        return None

    return response.json()

# WebSocket connection
def on_ws_message(ws, message):
    data = json.loads(message)
    print(f"Received: {data}")

def on_ws_error(ws, error):
    print(f"Error: {error}")

def on_ws_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_ws_open(ws):
    print("Connected to WebSocket")

def connect_websocket():
    ws_url = f"ws://localhost:8000/ws/live?api_key={API_KEY}"
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_ws_message,
        on_error=on_ws_error,
        on_close=on_ws_close,
        on_open=on_ws_open
    )
    ws.run_forever()
```

### cURL

```bash
# Get portfolio
curl -H "X-API-Key: rrr-your-key" \
  http://localhost:8000/api/portfolio

# Create position
curl -X POST \
  -H "X-API-Key: rrr-your-key" \
  http://localhost:8000/api/close-position/ETH

# Check usage
curl -H "X-API-Key: rrr-your-key" \
  http://localhost:8000/api/auth/usage

# Generate new key
curl -X POST \
  -H "X-API-Key: rrr-your-key" \
  "http://localhost:8000/api/auth/keys?name=production"
```

---

## Frontend Integration

The frontend needs to be updated to include the API key:

### 1. Update Environment Variables

Create `.env.local`:
```
VITE_API_KEY=rrr-your-key-here
VITE_API_URL=http://localhost:8000
```

### 2. Update API Client

Modify `frontend/src/api/client.ts`:
```typescript
const API_KEY = (import.meta as any).env.VITE_API_KEY || '';

export async function apiCall(endpoint: string, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...options.headers
  };

  const response = await fetch(
    `${API_BASE}${endpoint}`,
    { ...options, headers }
  );

  if (response.status === 401) {
    throw new Error('Invalid API key');
  }

  if (response.status === 429) {
    throw new Error('Rate limit exceeded');
  }

  return response.json();
}
```

### 3. Update WebSocket Hook

Modify `frontend/src/hooks/useWebSocket.ts`:
```typescript
const API_KEY = (import.meta as any).env.VITE_API_KEY || '';

export function useWebSocket() {
  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live?api_key=${API_KEY}`;

    ws = new WebSocket(wsUrl);

    ws.onerror = (event: Event) => {
      console.error('WebSocket error', event);
      // Handle 401 (invalid key) vs normal errors
    };
  };
}
```

---

## Configuration

### Environment Variables

Add to `.env`:
```bash
# CORS configuration (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# API key storage location (optional)
API_KEY_FILE=config/api_keys.json

# Rate limiting (optional, defaults shown)
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=10000
```

### Rate Limiting Customization

Modify `backend/api_server.py`:
```python
# Change default rate limits
rate_limiter = RateLimiter(
    requests_per_minute=200,      # Increase to 200/min
    requests_per_hour=20000       # Increase to 20000/hour
)
```

---

## Error Handling

### 401 Unauthorized

```json
{
  "detail": "Missing API key. Use X-API-Key header."
}
```

```json
{
  "detail": "Invalid or disabled API key"
}
```

**Solutions:**
- Ensure header is `X-API-Key` (case-sensitive)
- Check key is valid: `curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/auth/status`
- If key is disabled, create a new one

### 429 Rate Limited

```json
{
  "detail": "Rate limit exceeded. Resets at 2024-10-28T14:31:00.000000"
}
```

**Solutions:**
- Wait until reset time
- Check current usage: `curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/auth/usage`
- For WebSocket: Use exponential backoff for reconnection attempts
- Consider requesting higher limits if legitimate use case

### 503 Service Unavailable

```json
{
  "detail": "Dashboard not initialized"
}
```

**Solutions:**
- Ensure trading agent is running: `python3 run_trading.py`
- Check logs for startup errors
- Verify database exists: `ls -la logs/trading_data.db`

---

## Security Considerations

### API Key Best Practices

1. **Never commit keys to git**
   - Use `.env.local` for development
   - Use environment variables for production
   - Add `*.key` and `.env*` to `.gitignore`

2. **Rotate keys regularly**
   - Generate new keys periodically
   - Revoke old keys after rotation
   - Keep rotation log

3. **Limit key scope**
   - Different keys for different environments
   - Different keys for different clients if possible
   - Document which key is used for what

4. **Monitor key usage**
   - Check `last_used` timestamp
   - Review `request_count`
   - Alert on unusual patterns

### CORS Configuration

By default, only localhost is allowed:
```python
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
```

For production:
```bash
# Only allow frontend domain
CORS_ORIGINS=https://mytrading.example.com
```

### Rate Limiting

- **Per-key rate limiting** prevents one client from overwhelming system
- **Soft limits** allow temporary bursts
- **Hard limits** prevent abuse
- **WebSocket connections** count toward rate limits

---

## Testing

### Unit Tests

```python
import pytest
from auth import APIKeyManager, RateLimiter

def test_api_key_generation():
    manager = APIKeyManager()
    key = manager.generate_key("test")
    assert key.startswith("rrr-")
    assert manager.verify_key(key)

def test_api_key_revocation():
    manager = APIKeyManager()
    key = manager.generate_key("test")
    assert manager.verify_key(key)
    manager.revoke_key(key)
    assert not manager.verify_key(key)

def test_rate_limiting():
    limiter = RateLimiter(requests_per_minute=5)
    for i in range(5):
        allowed, _, _ = limiter.is_allowed("test-key")
        assert allowed
    # 6th request should be rejected
    allowed, _, _ = limiter.is_allowed("test-key")
    assert not allowed

def test_get_usage():
    limiter = RateLimiter()
    limiter.is_allowed("test-key")
    usage = limiter.get_usage("test-key")
    assert usage["requests_this_minute"] == 1
```

### Integration Tests

```bash
# Test API key authentication
curl -H "X-API-Key: invalid-key" \
  http://localhost:8000/api/portfolio
# Should return 401

# Test rate limiting
for i in {1..101}; do
  curl -H "X-API-Key: rrr-your-key" \
    http://localhost:8000/api/portfolio
done
# 101st request should return 429

# Test WebSocket with API key
wscat -c "ws://localhost:8000/ws/live?api_key=rrr-your-key"
```

---

## Monitoring & Logging

### Enable Debug Logging

```python
# In api_server.py
logging.basicConfig(level=logging.DEBUG)
```

### Log Events

All authentication events are logged:
```
[INFO] Authentication initialized at startup
[WARNING] Request attempted without API key
[WARNING] Invalid API key attempted
[WARNING] Rate limit exceeded for API key
[WARNING] WebSocket connection rejected: invalid API key
[WARNING] API key revoked: old_key
[WARNING] New API key generated: my_key
[INFO] WebSocket client connected with valid API key
```

### Monitor Key Usage

```python
# Get key statistics
manager = get_api_key_manager()
stats = manager.get_key_stats()
print(f"Total keys: {stats['total_keys']}")
print(f"Enabled: {stats['enabled_keys']}")
print(f"Disabled: {stats['disabled_keys']}")
print(f"Total requests: {stats['total_requests']}")

# Get individual key info
keys = manager.list_keys()
for key in keys:
    print(f"{key['name']}: last_used={key['last_used']}, requests={key['request_count']}")
```

---

## Common Issues & Solutions

### Issue: "Missing API key" on all requests

**Cause:** Frontend not sending X-API-Key header

**Solution:**
```typescript
// Make sure headers are set
const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY  // Add this
};

fetch(endpoint, { headers });
```

### Issue: "Invalid API key" with correct key

**Cause:** Key was revoked or hasn't been saved to config file

**Solution:**
```bash
# Check if config file exists and has keys
ls -la config/api_keys.json

# Generate new key
curl -X POST \
  -H "X-API-Key: rrr-default-key" \
  "http://localhost:8000/api/auth/keys?name=new_key"
```

### Issue: Rate limit hit too frequently

**Cause:** Normal requests exceeding limits, possibly due to polling frequency

**Solution:**
```python
# Reduce polling frequency in frontend
const UPDATE_INTERVAL = 5000; // ms between updates

# Or increase rate limits
rate_limiter = RateLimiter(
    requests_per_minute=500,
    requests_per_hour=50000
)
```

### Issue: WebSocket 4001 error

**Cause:** Missing API key in WebSocket URL

**Solution:**
```javascript
// Wrong: ws://localhost:8000/ws/live
// Right: ws://localhost:8000/ws/live?api_key=rrr-your-key

ws = new WebSocket(`ws://localhost:8000/ws/live?api_key=${API_KEY}`);
```

---

## Next Steps

### Your Action Items

1. ✅ **Run the system** (5 minutes)
   ```bash
   python3 run_trading.py
   ```

2. ✅ **Copy API key** (1 minute)
   - Check logs for generated default key
   - Save it to `.env.local`: `VITE_API_KEY=rrr-your-key`

3. ✅ **Test authentication** (2 minutes)
   ```bash
   curl -H "X-API-Key: rrr-your-key" http://localhost:8000/api/portfolio
   ```

4. ✅ **Update frontend** (5 minutes)
   - Add API key to environment variables
   - Update `frontend/src/api/client.ts` with key
   - Update `frontend/src/hooks/useWebSocket.ts` with key

5. ✅ **Verify frontend works** (2 minutes)
   - Start frontend: `npm run dev`
   - Check browser console for errors
   - Verify data loads

6. → **Proceed to Phase 3: Position Reconciliation** (Next)

### Phase 3 Will Address

- Position reconciliation with real exchange data
- Database persistence of positions
- Automatic recovery on restart
- Exchange API integration validation

**Estimated timeline:** 2-3 weeks

---

## Summary

**Phase 2 Achievements:**
- ✅ API key authentication with SHA-256 hashing
- ✅ Rate limiting (100 req/min, 10000 req/hour)
- ✅ Key management endpoints (create, list, revoke)
- ✅ WebSocket security integration
- ✅ CORS configuration
- ✅ Comprehensive error handling
- ✅ Full documentation and examples

**Result:**
- **Secure single-user system**
- **Protected against abuse**
- **Production-ready authentication**

---

**Generated:** October 28, 2024
**Author:** RRRv1 Development Team
**Status:** ✅ Ready for Phase 3
