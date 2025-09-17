#!/usr/bin/env python3
"""
Main entry point for the autonomous trading system.
This file is created for Railway deployment compatibility.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the autonomous system
from autonomous_system import main

if __name__ == "__main__":
    main()