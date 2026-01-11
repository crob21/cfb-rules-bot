"""
Cogs module for CFB 26 League Bot

Discord.py Cogs are modular extensions that group related commands together.
Each cog can be loaded/unloaded independently.

Available cogs:
- HSStatsCog: High school stats from MaxPreps (/hs group)
- CFBDataCog: College football data (/cfb group)
"""

from .hs_stats import HSStatsCog
from .cfb_data import CFBDataCog

__all__ = [
    'HSStatsCog',
    'CFBDataCog',
]

