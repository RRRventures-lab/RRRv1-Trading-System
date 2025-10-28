"""
API Authentication and Security for RRRv1 Trading Dashboard
Provides simple API key authentication for single-user system
"""

import os
import secrets
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
API_KEY_FILE = "config/api_keys.json"
API_KEY_HEADER = "X-API-Key"
API_KEY_LENGTH = 32  # Number of random bytes for API key


class APIKeyManager:
    """
    Manage API keys for authentication.
    Stores hashed keys for security (never stores plaintext).
    """

    def __init__(self, key_file: str = API_KEY_FILE):
        """
        Initialize API key manager.

        Args:
            key_file: Path to store API key hashes
        """
        self.key_file = key_file
        Path(self.key_file).parent.mkdir(parents=True, exist_ok=True)
        self._keys: Dict[str, Dict] = {}
        self._load_keys()

    def _hash_key(self, api_key: str) -> str:
        """
        Hash an API key for secure storage.

        Args:
            api_key: The API key to hash

        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _load_keys(self) -> None:
        """Load API keys from file."""
        try:
            if Path(self.key_file).exists():
                with open(self.key_file, 'r') as f:
                    self._keys = json.load(f)
                logger.info(f"Loaded {len(self._keys)} API keys from {self.key_file}")
            else:
                self._keys = {}
                logger.info("No existing API keys found")
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            self._keys = {}

    def _save_keys(self) -> None:
        """Save API keys to file."""
        try:
            Path(self.key_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, 'w') as f:
                json.dump(self._keys, f, indent=2)
            # Restrict file permissions to owner only
            os.chmod(self.key_file, 0o600)
            logger.debug(f"Saved API keys to {self.key_file}")
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")

    def generate_key(self, name: str = "default") -> str:
        """
        Generate a new API key.

        Args:
            name: Name/description for the key

        Returns:
            The generated API key (plaintext - only shown once!)
        """
        # Generate random API key
        api_key = f"rrr-{secrets.token_hex(API_KEY_LENGTH // 2)}"

        # Hash for storage
        key_hash = self._hash_key(api_key)

        # Store metadata
        self._keys[key_hash] = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "enabled": True,
            "request_count": 0
        }

        self._save_keys()
        logger.info(f"Generated new API key: {name}")

        return api_key

    def verify_key(self, api_key: str) -> bool:
        """
        Verify if an API key is valid.

        Args:
            api_key: The API key to verify

        Returns:
            True if key is valid and enabled, False otherwise
        """
        key_hash = self._hash_key(api_key)

        if key_hash not in self._keys:
            logger.warning(f"Invalid API key attempted")
            return False

        key_info = self._keys[key_hash]

        if not key_info.get("enabled", False):
            logger.warning(f"Disabled API key used: {key_info.get('name')}")
            return False

        # Update last used timestamp
        self._keys[key_hash]["last_used"] = datetime.utcnow().isoformat()
        self._keys[key_hash]["request_count"] = key_info.get("request_count", 0) + 1
        self._save_keys()

        return True

    def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key (disable it).

        Args:
            api_key: The API key to revoke

        Returns:
            True if revoked, False if not found
        """
        key_hash = self._hash_key(api_key)

        if key_hash not in self._keys:
            logger.error(f"API key not found for revocation")
            return False

        self._keys[key_hash]["enabled"] = False
        self._save_keys()
        logger.info(f"API key revoked: {self._keys[key_hash].get('name')}")

        return True

    def list_keys(self) -> list:
        """
        List all API keys (without showing the actual keys).

        Returns:
            List of key metadata
        """
        keys_list = []
        for key_hash, info in self._keys.items():
            keys_list.append({
                "name": info.get("name"),
                "created_at": info.get("created_at"),
                "last_used": info.get("last_used"),
                "enabled": info.get("enabled"),
                "request_count": info.get("request_count", 0)
            })
        return keys_list

    def get_key_stats(self) -> Dict:
        """Get statistics about API keys."""
        total_keys = len(self._keys)
        enabled_keys = sum(1 for k in self._keys.values() if k.get("enabled", False))
        total_requests = sum(k.get("request_count", 0) for k in self._keys.values())

        return {
            "total_keys": total_keys,
            "enabled_keys": enabled_keys,
            "disabled_keys": total_keys - enabled_keys,
            "total_requests": total_requests
        }


class RateLimiter:
    """
    Simple rate limiter for API requests.
    Tracks requests per key and enforces limits.
    """

    def __init__(self, requests_per_minute: int = 100, requests_per_hour: int = 10000):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._request_log: Dict[str, list] = {}  # api_key -> [(timestamp, endpoint), ...]

    def is_allowed(self, api_key: str, endpoint: str = None) -> tuple:
        """
        Check if a request is allowed under rate limits.

        Args:
            api_key: The API key making the request
            endpoint: The endpoint being accessed (optional)

        Returns:
            Tuple of (is_allowed: bool, remaining_requests: int, reset_time: datetime)
        """
        now = datetime.utcnow()

        if api_key not in self._request_log:
            self._request_log[api_key] = []

        # Clean up old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        self._request_log[api_key] = [
            (ts, ep) for ts, ep in self._request_log[api_key]
            if ts > hour_ago
        ]

        # Check minute limit
        recent_minute = [
            (ts, ep) for ts, ep in self._request_log[api_key]
            if ts > minute_ago
        ]

        if len(recent_minute) >= self.requests_per_minute:
            remaining = max(0, self.requests_per_minute - len(recent_minute))
            reset_time = recent_minute[0][0] + timedelta(minutes=1)
            return False, remaining, reset_time

        # Check hour limit
        if len(self._request_log[api_key]) >= self.requests_per_hour:
            remaining = max(0, self.requests_per_hour - len(self._request_log[api_key]))
            reset_time = self._request_log[api_key][0][0] + timedelta(hours=1)
            return False, remaining, reset_time

        # Request allowed, log it
        self._request_log[api_key].append((now, endpoint))
        remaining = self.requests_per_minute - len(recent_minute) - 1

        return True, remaining, now + timedelta(minutes=1)

    def get_usage(self, api_key: str) -> Dict:
        """Get request usage for an API key."""
        if api_key not in self._request_log:
            return {
                "requests_this_minute": 0,
                "requests_this_hour": 0,
                "limit_minute": self.requests_per_minute,
                "limit_hour": self.requests_per_hour
            }

        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        requests_minute = sum(
            1 for ts, _ in self._request_log[api_key]
            if ts > minute_ago
        )
        requests_hour = sum(
            1 for ts, _ in self._request_log[api_key]
            if ts > hour_ago
        )

        return {
            "requests_this_minute": requests_minute,
            "requests_this_hour": requests_hour,
            "limit_minute": self.requests_per_minute,
            "limit_hour": self.requests_per_hour,
            "minute_remaining": max(0, self.requests_per_minute - requests_minute),
            "hour_remaining": max(0, self.requests_per_hour - requests_hour)
        }


# Global instances
_api_key_manager: Optional[APIKeyManager] = None
_rate_limiter: Optional[RateLimiter] = None


def get_api_key_manager() -> APIKeyManager:
    """Get or create the API key manager."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def get_rate_limiter() -> RateLimiter:
    """Get or create the rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=100,
            requests_per_hour=10000
        )
    return _rate_limiter


def initialize_default_key() -> None:
    """
    Initialize a default API key if none exists.
    This is called on startup if no keys are configured.
    """
    manager = get_api_key_manager()

    if len(manager._keys) == 0:
        api_key = manager.generate_key("default")
        logger.warning(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          INITIAL API KEY GENERATED                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

A default API key has been generated for you.

API Key: {api_key}

⚠️  SAVE THIS KEY SECURELY - IT WILL NOT BE SHOWN AGAIN!

Add to your environment or .env file:
    export API_KEY="{api_key}"

Or pass it in requests:
    curl -H "X-API-Key: {api_key}" http://localhost:8000/api/portfolio

The key has been stored in: {API_KEY_FILE}

╚══════════════════════════════════════════════════════════════════════════════╝
        """)
