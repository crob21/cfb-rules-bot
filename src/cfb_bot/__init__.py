"""
CFB Rules Bot - A Discord bot for College Football 26 Online Dynasty League

Architecture: Cog-based modular design (v2.0)
"""

__version__ = "3.0.0"

# Import the main bot function
# v3.0: Now using cog-based architecture (bot_main.py)
# Original monolithic bot.py is kept as fallback reference
from .bot_main import run as main

__all__ = ["main"]
