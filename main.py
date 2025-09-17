#!/usr/bin/env python3
"""
CFB Rules Bot - Main Entry Point

A Discord bot for College Football 26 Online Dynasty League
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cfb_bot import main

if __name__ == "__main__":
    # Run the bot
    main()
