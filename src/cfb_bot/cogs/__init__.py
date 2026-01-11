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
- AIChatCog: AI-powered chat commands (/harry, /ask, /summarize)
- CoreCog: Always-available core commands (/help, /version, etc.)
"""

from .hs_stats import HSStatsCog
from .cfb_data import CFBDataCog
from .recruiting import RecruitingCog
from .charter import CharterCog
from .league import LeagueCog
from .admin import AdminCog
from .ai_chat import AIChatCog
from .core import CoreCog

__all__ = [
    'HSStatsCog',
    'CFBDataCog',
    'RecruitingCog',
    'CharterCog',
    'LeagueCog',
    'AdminCog',
    'AIChatCog',
    'CoreCog',
]
