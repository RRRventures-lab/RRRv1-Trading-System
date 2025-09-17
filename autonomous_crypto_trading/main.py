#!/usr/bin/env python3
"""
Main entry point for the advanced multi-agent trading system.
Ultra-fast execution with AI agent swarm for competitive edge.
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check for multi-agent mode
if os.getenv('ULTRA_FAST_MODE', 'false').lower() == 'true':
    # Use advanced multi-agent system
    from multi_agent_system import main as multi_agent_main

    if __name__ == "__main__":
        asyncio.run(multi_agent_main())
else:
    # Use original system for compatibility
    from autonomous_system import main as original_main

    if __name__ == "__main__":
        original_main()