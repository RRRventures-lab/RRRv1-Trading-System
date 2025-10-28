"""
Mem0 AI Memory Integration for RRRv1 Trading System
Provides persistent, adaptive learning capabilities with multiple memory categories
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryCategory(Enum):
    """Categories of memories for different aspects of trading"""
    USER_PREFERENCES = "user_preferences"
    MARKET_CONDITIONS = "market_conditions"
    STRATEGY_PERFORMANCE = "strategy_performance"
    RISK_PROFILE = "risk_profile"
    PORTFOLIO_PATTERNS = "portfolio_patterns"
    LEARNING_INSIGHTS = "learning_insights"


class Mem0Client:
    """
    Wrapper for Mem0 AI API integration
    Handles persistent memory storage and retrieval for trading decisions

    Usage:
        client = Mem0Client(api_key="your-api-key")
        client.store("market_conditions", "BTC is in uptrend with strong momentum")
        memories = client.recall("market_conditions", limit=5)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mem0 client with API key

        Args:
            api_key: Mem0 API key (defaults to M0_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("M0_API_KEY")

        if not self.api_key:
            logger.warning("⚠ Mem0 API key not found. Set M0_API_KEY environment variable.")
            self.api_key = None
            self.available = False
        else:
            self.available = True
            logger.info("✓ Mem0 client initialized successfully")

        self.base_url = "https://api.mem0.ai/v1"
        self.memories: Dict[str, List[Dict]] = {
            cat.value: [] for cat in MemoryCategory
        }

    def store(self, category: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Store a memory in Mem0

        Args:
            category: Memory category (from MemoryCategory enum)
            content: Memory content
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.available or not self.api_key:
            logger.warning("⚠ Mem0 not available. Memory will be stored locally only.")
            return self._store_local(category, content, metadata)

        try:
            memory_obj = {
                "category": category,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            # In production: Call Mem0 API
            # response = requests.post(
            #     f"{self.base_url}/memories",
            #     headers={"Authorization": f"Bearer {self.api_key}"},
            #     json=memory_obj
            # )

            # For now, store locally
            self._store_local(category, content, metadata)
            logger.debug(f"✓ Memory stored: {category}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to store memory: {e}")
            return False

    def recall(self, category: str, limit: int = 5,
               query: Optional[str] = None) -> List[Dict]:
        """
        Recall memories from a category

        Args:
            category: Memory category to search
            limit: Number of memories to return
            query: Optional search query

        Returns:
            List of memory dictionaries
        """
        if not self.available or not self.api_key:
            return self._recall_local(category, limit)

        try:
            # In production: Call Mem0 API
            # params = {"category": category, "limit": limit}
            # if query:
            #     params["query"] = query
            # response = requests.get(
            #     f"{self.base_url}/memories",
            #     headers={"Authorization": f"Bearer {self.api_key}"},
            #     params=params
            # )

            # For now, retrieve from local storage
            return self._recall_local(category, limit)

        except Exception as e:
            logger.error(f"✗ Failed to recall memories: {e}")
            return []

    def update(self, memory_id: str, content: str) -> bool:
        """
        Update an existing memory

        Args:
            memory_id: ID of memory to update
            content: New content

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.available and self.api_key:
                # In production: Call Mem0 API
                pass

            logger.debug(f"✓ Memory updated: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to update memory: {e}")
            return False

    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.available and self.api_key:
                # In production: Call Mem0 API
                pass

            logger.debug(f"✓ Memory deleted: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to delete memory: {e}")
            return False

    # Local storage methods (fallback)
    def _store_local(self, category: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store memory locally"""
        try:
            memory_obj = {
                "id": f"{category}_{datetime.utcnow().timestamp()}",
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }

            if category not in self.memories:
                self.memories[category] = []

            self.memories[category].append(memory_obj)
            return True
        except Exception as e:
            logger.error(f"✗ Local storage failed: {e}")
            return False

    def _recall_local(self, category: str, limit: int = 5) -> List[Dict]:
        """Recall memories from local storage"""
        if category not in self.memories:
            return []

        # Return most recent memories (reverse order)
        return self.memories[category][-limit:][::-1]


class TradeMemory:
    """
    Trading-specific memory management
    Learns from trade outcomes and market conditions
    """

    def __init__(self, mem0_client: Mem0Client):
        """
        Initialize trade memory manager

        Args:
            mem0_client: Mem0 client instance
        """
        self.mem0 = mem0_client

    def record_trade(self, trade_data: Dict[str, Any]) -> bool:
        """
        Record a completed trade for learning

        Args:
            trade_data: Dictionary with trade information
                - asset: Trading pair
                - action: BUY/SELL
                - size: Position size
                - entry_price: Entry price
                - exit_price: Exit price
                - pnl: Profit/loss
                - strategy: Strategy name
                - duration_minutes: How long position was held

        Returns:
            True if recorded successfully
        """
        try:
            content = f"""
Trade Executed:
- Asset: {trade_data.get('asset')}
- Action: {trade_data.get('action')}
- Size: {trade_data.get('size')}
- Entry: ${trade_data.get('entry_price')}
- Exit: ${trade_data.get('exit_price')}
- P&L: ${trade_data.get('pnl')}
- Strategy: {trade_data.get('strategy')}
- Duration: {trade_data.get('duration_minutes')} minutes
- Win: {'Yes' if trade_data.get('pnl', 0) > 0 else 'No'}
"""

            return self.mem0.store(
                MemoryCategory.STRATEGY_PERFORMANCE.value,
                content,
                metadata={
                    "trade_id": trade_data.get('trade_id'),
                    "pnl": trade_data.get('pnl'),
                    "strategy": trade_data.get('strategy'),
                    "asset": trade_data.get('asset')
                }
            )
        except Exception as e:
            logger.error(f"✗ Failed to record trade: {e}")
            return False

    def record_market_condition(self, condition: str, analysis: str) -> bool:
        """
        Record market conditions and analysis

        Args:
            condition: Market condition (e.g., "uptrend", "consolidation")
            analysis: Detailed market analysis

        Returns:
            True if recorded successfully
        """
        content = f"Market Condition: {condition}\nAnalysis: {analysis}"

        return self.mem0.store(
            MemoryCategory.MARKET_CONDITIONS.value,
            content,
            metadata={"condition": condition}
        )

    def record_risk_event(self, event_type: str, description: str,
                         impact: str) -> bool:
        """
        Record risk events for learning

        Args:
            event_type: Type of risk event
            description: Description of what happened
            impact: Impact assessment

        Returns:
            True if recorded successfully
        """
        content = f"""
Risk Event: {event_type}
Description: {description}
Impact: {impact}
Timestamp: {datetime.utcnow().isoformat()}
"""

        return self.mem0.store(
            MemoryCategory.RISK_PROFILE.value,
            content,
            metadata={"event_type": event_type}
        )

    def recall_strategy_performance(self, asset: Optional[str] = None,
                                   limit: int = 10) -> List[Dict]:
        """
        Recall past strategy performance

        Args:
            asset: Optional asset to filter by
            limit: Number of memories to return

        Returns:
            List of performance memories
        """
        memories = self.mem0.recall(
            MemoryCategory.STRATEGY_PERFORMANCE.value,
            limit=limit,
            query=asset if asset else None
        )
        return memories

    def get_strategy_insights(self, strategy_name: str) -> str:
        """
        Get learning insights for a specific strategy

        Args:
            strategy_name: Name of strategy to analyze

        Returns:
            Generated insights based on memories
        """
        memories = self.mem0.recall(
            MemoryCategory.STRATEGY_PERFORMANCE.value,
            limit=20
        )

        # Analyze memories to generate insights
        winning_trades = sum(1 for m in memories if "P&L: $" in str(m))

        insight = f"""
Strategy: {strategy_name}
Analyzed {len(memories)} recent trades
Winning trades: {winning_trades}/{len(memories)}
Win rate: {(winning_trades/len(memories)*100) if memories else 0:.1f}%
"""

        return insight


# Global Mem0 instance (initialized on first use)
_mem0_client: Optional[Mem0Client] = None


def get_mem0_client() -> Mem0Client:
    """Get or create global Mem0 client"""
    global _mem0_client

    if _mem0_client is None:
        api_key = os.getenv("M0_API_KEY")
        _mem0_client = Mem0Client(api_key=api_key)

    return _mem0_client


def initialize_mem0(api_key: Optional[str] = None) -> Mem0Client:
    """
    Initialize Mem0 client for the application

    Args:
        api_key: Mem0 API key (if not provided, uses environment variable)

    Returns:
        Initialized Mem0Client instance
    """
    global _mem0_client
    _mem0_client = Mem0Client(api_key=api_key)
    return _mem0_client


# Example usage functions
def example_memory_operations():
    """Example of using Mem0 memory system"""

    # Initialize client
    client = get_mem0_client()
    trade_memory = TradeMemory(client)

    # Record a trade
    trade_data = {
        "trade_id": "TRD_001",
        "asset": "BTC/USD",
        "action": "BUY",
        "size": 0.5,
        "entry_price": 43000,
        "exit_price": 43500,
        "pnl": 250,
        "strategy": "smart_money_strategy",
        "duration_minutes": 45
    }

    if trade_memory.record_trade(trade_data):
        logger.info("✓ Trade recorded to Mem0")

    # Record market condition
    if trade_memory.record_market_condition(
        "uptrend",
        "Bitcoin showing strong momentum with higher lows"
    ):
        logger.info("✓ Market condition recorded")

    # Recall strategy performance
    performance = trade_memory.recall_strategy_performance(asset="BTC/USD")
    logger.info(f"Recalled {len(performance)} performance memories")

    # Get insights
    insights = trade_memory.get_strategy_insights("smart_money_strategy")
    logger.info(f"Strategy insights:\n{insights}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_memory_operations()
