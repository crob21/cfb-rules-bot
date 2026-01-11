# Bot Refactor Plan: OOP with Cogs

**Goal:** Transform 7,200-line `bot.py` into maintainable, modular codebase  
**Estimated Time:** 2-3 hours  
**Risk:** Medium (test thoroughly before deploying)

---

## Current State

```
bot.py (7,217 lines)
├── 106 commands/handlers
├── 6 event handlers (on_ready, on_message, etc.)
├── Global variables scattered throughout
├── Hard to test, maintain, or extend
└── Single point of failure
```

---

## Target Architecture

```
src/cfb_bot/
├── bot.py (~150 lines)              # Bot setup, cog loading
├── config.py (~50 lines)            # Constants, colors, footers
│
├── cogs/
│   ├── __init__.py                  # Cog exports
│   ├── core.py (~400 lines)         # Events, /help, /version, /whats_new
│   ├── recruiting.py (~500 lines)   # /recruiting group (6 commands)
│   ├── cfb_data.py (~600 lines)     # /cfb group (9 commands)
│   ├── hs_stats.py (~300 lines)     # /hs group (2 commands)
│   ├── league.py (~800 lines)       # /league group (19 commands)
│   ├── charter.py (~400 lines)      # /charter group (10 commands)
│   ├── admin.py (~700 lines)        # /admin group (14 commands)
│   └── ai_chat.py (~600 lines)      # /harry, /ask, /summarize, @mentions
│
├── services/
│   ├── __init__.py
│   ├── checks.py (~100 lines)       # Module/channel permission checks
│   └── embeds.py (~150 lines)       # Common embed builders
│
└── utils/                           # (existing - no changes needed)
    ├── server_config.py
    ├── on3_scraper.py
    ├── recruiting_scraper.py
    ├── hs_stats_scraper.py
    ├── timekeeper.py
    ├── charter_editor.py
    ├── version_manager.py
    └── ...
```

---

## Cog Breakdown

### 1. `cogs/core.py` - Core Bot Functionality
**Events:**
- `on_ready` - Startup, sync commands, send notifications
- `on_guild_join` / `on_guild_remove` - Guild tracking
- `on_command_error` - Error handling

**Commands:**
- `/help` - Dynamic help based on enabled modules
- `/version` - Current version
- `/changelog` - Version history
- `/whats_new` - Latest features
- `/tokens` - AI token stats

**Shared State:**
- Bot startup time
- Guild count tracking

---

### 2. `cogs/recruiting.py` - Recruiting Data
**Group:** `/recruiting`

**Commands:**
- `player` - Look up a recruit
- `top` - Top recruits by position/state
- `class` - Team recruiting class
- `commits` - Team's committed recruits
- `rankings` - Top 25 team rankings
- `source` - Switch On3/247 source

**Dependencies:**
- `on3_scraper.py`
- `recruiting_scraper.py`
- `server_config.py` (for source preference)

---

### 3. `cogs/cfb_data.py` - College Football Data
**Group:** `/cfb`

**Commands:**
- `player` / `players` - Player lookup
- `rankings` - AP/Coaches/CFP polls
- `schedule` - Team schedules
- `matchup` - Head-to-head history
- `transfers` - Portal activity
- `draft` - NFL draft picks
- `betting` - Game lines
- `ratings` - SP+/SRS/Elo
- `records` - Historical records

**Dependencies:**
- `cfb_data.py` utility

---

### 4. `cogs/hs_stats.py` - High School Stats
**Group:** `/hs`

**Commands:**
- `stats` - Single player lookup
- `bulk` - Multiple players

**Dependencies:**
- `hs_stats_scraper.py`

---

### 5. `cogs/league.py` - League Management
**Group:** `/league`

**Commands (19 total):**
- **Staff:** `staff`, `set_owner`, `set_commish`, `pick_commish`
- **Season:** `week`, `weeks`, `games`, `find_game`, `byes`, `set_week`
- **Timer:** `timer`, `timer_status`, `timer_stop`, `timer_channel`
- **Info:** `team`, `rules`, `dynasty`
- **Fun:** `nag`, `stop_nag`

**Dependencies:**
- `timekeeper.py`
- `schedule_manager.py`

---

### 6. `cogs/charter.py` - Charter Management
**Group:** `/charter`

**Commands:**
- `lookup` - Find a rule
- `link` - Charter URL
- `scan` - Scan channel for votes
- `sync` - Sync to Discord
- `history` - Recent changes
- `search` - Search charter text
- `add` - Add new rule
- `update` - Update existing rule
- `backups` - List backups
- `restore` - Restore from backup

**Dependencies:**
- `charter_editor.py`
- `google_docs.py` (if available)

---

### 7. `cogs/admin.py` - Bot Administration
**Group:** `/admin`

**Commands:**
- `config` - View/enable/disable modules
- `channels` - Manage channel permissions
- `set_channel` - Set admin channel
- `add` / `remove` - Manage bot admins
- `block` / `unblock` - Block channels
- `list` - List admins
- `sync` - Force command sync

**Dependencies:**
- `server_config.py`
- `admin_manager.py`

---

### 8. `cogs/ai_chat.py` - AI Conversations
**Standalone Commands:**
- `/harry` - CFB/league questions
- `/ask` - General AI questions
- `/summarize` - Channel summaries

**Event Handling:**
- `on_message` listener for @mentions
- Auto-responses (Fuck Oregon!, etc.)
- League-related question detection

**Dependencies:**
- `ai_assistant.py`
- `channel_summarizer.py`

---

## Shared Services

### `services/checks.py`
```python
async def check_module_enabled(interaction, module: FeatureModule) -> bool:
    """Check if module is enabled and channel is whitelisted"""
    ...

async def check_module_enabled_deferred(interaction, module: FeatureModule) -> bool:
    """Same but for deferred interactions"""
    ...

def is_admin(user, interaction) -> bool:
    """Check if user is bot admin"""
    ...
```

### `services/embeds.py`
```python
class EmbedBuilder:
    @staticmethod
    def success(title, description) -> discord.Embed: ...
    
    @staticmethod
    def error(title, description) -> discord.Embed: ...
    
    @staticmethod
    def warning(title, description) -> discord.Embed: ...
```

---

## Migration Steps

### Phase 1: Setup (15 min)
1. Create `cogs/` and `services/` directories
2. Create `config.py` with Colors, Footers constants
3. Create `services/checks.py` with permission helpers
4. Create `services/embeds.py` with embed builders

### Phase 2: Extract Cogs (90 min)
Extract in this order (least dependencies first):

1. **hs_stats.py** (~15 min) - Simplest, 2 commands
2. **cfb_data.py** (~15 min) - Self-contained
3. **recruiting.py** (~15 min) - Self-contained
4. **charter.py** (~15 min) - Moderate complexity
5. **league.py** (~15 min) - Many commands but straightforward
6. **admin.py** (~15 min) - Config management
7. **ai_chat.py** (~20 min) - Most complex (on_message logic)
8. **core.py** (~15 min) - Events and remaining commands

### Phase 3: Update bot.py (15 min)
```python
# bot.py - Final form
import discord
from discord.ext import commands

from .config import TOKEN
from .cogs import (
    CoreCog, RecruitingCog, CFBDataCog, HSStatsCog,
    LeagueCog, CharterCog, AdminCog, AIChatCog
)

bot = commands.Bot(...)

async def main():
    await bot.add_cog(CoreCog(bot))
    await bot.add_cog(RecruitingCog(bot))
    # ... etc
    await bot.start(TOKEN)
```

### Phase 4: Test (30 min)
1. Test each cog in isolation
2. Test module enable/disable
3. Test channel permissions
4. Test error handling
5. Full integration test

---

## Cog Template

```python
# cogs/example.py
import discord
from discord import app_commands
from discord.ext import commands
import logging

from ..services.checks import check_module_enabled
from ..utils.server_config import FeatureModule

logger = logging.getLogger('CFB26Bot.Example')


class ExampleCog(commands.Cog):
    """Description of what this cog does"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # Define command group
    example_group = app_commands.Group(
        name="example",
        description="Example commands"
    )
    
    @example_group.command(name="test")
    async def test_command(self, interaction: discord.Interaction):
        """Test command description"""
        if not await check_module_enabled(interaction, FeatureModule.EXAMPLE):
            return
        
        await interaction.response.send_message("Hello!")
    
    # Event listeners
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle messages if needed"""
        pass


async def setup(bot: commands.Bot):
    """Required setup function for loading cog"""
    await bot.add_cog(ExampleCog(bot))
```

---

## Rollback Plan

If something breaks:
1. Git revert to pre-refactor commit
2. Redeploy old `bot.py`
3. Debug in development

Keep the old `bot.py` as `bot_legacy.py` until confirmed working.

---

## Post-Refactor Benefits

- ✅ Each file < 800 lines
- ✅ Clear separation of concerns
- ✅ Easy to add new features
- ✅ Testable in isolation
- ✅ Multiple contributors can work simultaneously
- ✅ Hot-reload individual cogs (future)
- ✅ Better error isolation

---

## Questions to Resolve Before Starting

1. **Keep backward compatibility?** - Command names stay the same ✓
2. **Database in future?** - Current Discord DM storage works fine
3. **Testing framework?** - Optional, can add pytest later
4. **Type hints?** - Yes, add throughout

---

*Plan created: January 11, 2026*  
*Ready to execute when you are! 🚀*

