"""
Cogs module for CFB 26 League Bot

Discord.py Cogs are modular extensions that group related commands together.
Each cog can be loaded/unloaded independently.

Available cogs:
- HSStatsCog: High school stats from MaxPreps (/hs group)
- CFBDataCog: College football data (/cfb group)
- RecruitingCog: Recruiting data (/recruiting group)
- CharterCog: League charter management (/charter group)
- LeagueCog: League management (/league group)
- AdminCog: Admin commands (/admin group)
"""

from .hs_stats import HSStatsCog
from .cfb_data import CFBDataCog
from .recruiting import RecruitingCog
from .charter import CharterCog
from .league import LeagueCog
from .admin import AdminCog

__all__ = [
    'HSStatsCog',
    'CFBDataCog',
    'RecruitingCog',
    'CharterCog',
    'LeagueCog',
    'AdminCog',
]
