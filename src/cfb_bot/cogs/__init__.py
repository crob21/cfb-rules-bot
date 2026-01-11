"""
Cogs module for CFB 26 League Bot

Discord.py Cogs are modular extensions that group related commands together.
Each cog can be loaded/unloaded independently.

Available cogs:
- HSStatsCog: High school stats from MaxPreps (/hs group)
- (more to come)
"""

from .hs_stats import HSStatsCog

__all__ = [
    'HSStatsCog',
]

