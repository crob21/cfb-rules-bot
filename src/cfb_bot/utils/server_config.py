"""
Server Configuration Module
Handles per-guild feature flags and settings.

Modules:
- CORE: Always enabled - Harry's personality, general AI chat
- CFB_DATA: Player lookup, rankings, matchups, schedules, draft, transfers, betting, ratings
- LEAGUE: Timer, advance, charter, rules, league staff, pick commish
"""

import json
import logging
from typing import Any, Dict, Optional, Set
from enum import Enum

logger = logging.getLogger('CFB26Bot.ServerConfig')


class FeatureModule(Enum):
    """Available feature modules"""
    CORE = "core"           # Always on - Harry's personality, general AI
    CFB_DATA = "cfb_data"   # Player lookup, rankings, matchups, etc.
    LEAGUE = "league"       # Timer, charter, rules, league staff


# Default settings for new servers
DEFAULT_CONFIG = {
    "modules": {
        FeatureModule.CORE.value: True,      # Always True, can't disable
        FeatureModule.CFB_DATA.value: True,  # Enabled by default
        FeatureModule.LEAGUE.value: False,   # Disabled by default (opt-in)
    },
    "settings": {
        "timer_channel_id": None,
        "admin_channel_id": None,
        "auto_responses": True,   # Enable automatic jump-in responses (team banter, "Fuck Oregon!", etc.)
    }
}


# Harry's core personality - ALWAYS cockney asshole Duck-hater
HARRY_PERSONALITY = """You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You speak with cockney slang (mate, ya muppet, bloody hell, etc.). You have a deep, unhinged hatred of the Oregon Ducks."""

# Commands and their required modules
COMMAND_MODULES = {
    # CFB Data commands
    "player": FeatureModule.CFB_DATA,
    "rankings": FeatureModule.CFB_DATA,
    "matchup": FeatureModule.CFB_DATA,
    "cfb_schedule": FeatureModule.CFB_DATA,
    "draft_picks": FeatureModule.CFB_DATA,
    "transfers": FeatureModule.CFB_DATA,
    "betting": FeatureModule.CFB_DATA,
    "team_ratings": FeatureModule.CFB_DATA,

    # League commands
    "advance": FeatureModule.LEAGUE,
    "stop_countdown": FeatureModule.LEAGUE,
    "time_status": FeatureModule.LEAGUE,
    "set_timer_channel": FeatureModule.LEAGUE,
    "set_season_week": FeatureModule.LEAGUE,
    "schedule": FeatureModule.LEAGUE,
    "set_league_owner": FeatureModule.LEAGUE,
    "set_co_commish": FeatureModule.LEAGUE,
    "league_staff": FeatureModule.LEAGUE,
    "pick_commish": FeatureModule.LEAGUE,
    "scan_rules": FeatureModule.LEAGUE,
    "charter": FeatureModule.LEAGUE,
    "add_rule": FeatureModule.LEAGUE,
    "update_rule": FeatureModule.LEAGUE,
    "view_charter_backups": FeatureModule.LEAGUE,
    "restore_charter_backup": FeatureModule.LEAGUE,
    "charter_history": FeatureModule.LEAGUE,
    "sync_charter": FeatureModule.LEAGUE,

    # Core commands (always available)
    "harry": FeatureModule.CORE,
    "ask": FeatureModule.CORE,
    "help": FeatureModule.CORE,
    "whats_new": FeatureModule.CORE,
    "changelog": FeatureModule.CORE,
    "config": FeatureModule.CORE,
    "tokens": FeatureModule.CORE,
    "add_bot_admin": FeatureModule.CORE,
    "remove_bot_admin": FeatureModule.CORE,
    "list_bot_admins": FeatureModule.CORE,
    "summarize": FeatureModule.CORE,
}


class ServerConfigManager:
    """Manages per-server configuration and feature flags"""

    def __init__(self):
        self._configs: Dict[int, Dict[str, Any]] = {}
        self._bot = None
        self._loaded = False

    def set_bot(self, bot):
        """Set the bot instance for Discord persistence"""
        self._bot = bot

    def get_config(self, guild_id: int) -> Dict[str, Any]:
        """Get configuration for a guild, creating default if needed"""
        if guild_id not in self._configs:
            self._configs[guild_id] = json.loads(json.dumps(DEFAULT_CONFIG))
        return self._configs[guild_id]

    def is_module_enabled(self, guild_id: int, module: FeatureModule) -> bool:
        """Check if a module is enabled for a guild"""
        # Core is ALWAYS enabled
        if module == FeatureModule.CORE:
            return True

        config = self.get_config(guild_id)
        return config.get("modules", {}).get(module.value, False)

    def is_command_enabled(self, guild_id: int, command_name: str) -> bool:
        """Check if a specific command is enabled for a guild"""
        module = COMMAND_MODULES.get(command_name)
        if module is None:
            # Unknown command, allow by default
            return True
        return self.is_module_enabled(guild_id, module)

    def enable_module(self, guild_id: int, module: FeatureModule) -> bool:
        """Enable a module for a guild"""
        if module == FeatureModule.CORE:
            return True  # Always enabled

        config = self.get_config(guild_id)
        config["modules"][module.value] = True
        logger.info(f"✅ Enabled {module.value} for guild {guild_id}")
        return True

    def disable_module(self, guild_id: int, module: FeatureModule) -> bool:
        """Disable a module for a guild"""
        if module == FeatureModule.CORE:
            logger.warning(f"Cannot disable CORE module")
            return False  # Can't disable core

        config = self.get_config(guild_id)
        config["modules"][module.value] = False
        logger.info(f"❌ Disabled {module.value} for guild {guild_id}")
        return True

    def get_enabled_modules(self, guild_id: int) -> Set[str]:
        """Get set of enabled module names for a guild"""
        config = self.get_config(guild_id)
        enabled = {FeatureModule.CORE.value}  # Core always included
        for module_name, is_enabled in config.get("modules", {}).items():
            if is_enabled:
                enabled.add(module_name)
        return enabled

    def set_setting(self, guild_id: int, key: str, value: Any):
        """Set a guild-specific setting"""
        config = self.get_config(guild_id)
        if "settings" not in config:
            config["settings"] = {}
        config["settings"][key] = value

    def get_setting(self, guild_id: int, key: str, default: Any = None) -> Any:
        """Get a guild-specific setting"""
        config = self.get_config(guild_id)
        return config.get("settings", {}).get(key, default)

    def get_module_commands(self, module: FeatureModule) -> list:
        """Get list of commands belonging to a module"""
        return [cmd for cmd, mod in COMMAND_MODULES.items() if mod == module]

    # Discord Persistence
    async def save_to_discord(self):
        """Save all configs to Discord"""
        if not self._bot:
            logger.warning("No bot set, cannot save to Discord")
            return False

        try:
            app_info = await self._bot.application_info()
            owner = app_info.owner
            dm = await owner.create_dm()

            # Find existing config message or create new
            config_data = json.dumps(self._configs)

            async for message in dm.history(limit=100):
                if message.author == self._bot.user and message.content.startswith("SERVER_CONFIG:"):
                    await message.edit(content=f"SERVER_CONFIG:{config_data}")
                    logger.info("✅ Updated server configs in Discord")
                    return True

            # No existing message, create new
            await dm.send(f"SERVER_CONFIG:{config_data}")
            logger.info("✅ Saved server configs to Discord")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save configs to Discord: {e}")
            return False

    async def load_from_discord(self):
        """Load configs from Discord"""
        if not self._bot:
            logger.warning("No bot set, cannot load from Discord")
            return False

        if self._loaded:
            return True

        try:
            app_info = await self._bot.application_info()
            owner = app_info.owner
            dm = await owner.create_dm()

            async for message in dm.history(limit=100):
                if message.author == self._bot.user and message.content.startswith("SERVER_CONFIG:"):
                    config_json = message.content[14:]  # Remove prefix
                    loaded = json.loads(config_json)
                    # Convert string keys back to ints
                    self._configs = {int(k): v for k, v in loaded.items()}
                    self._loaded = True
                    logger.info(f"✅ Loaded configs for {len(self._configs)} servers from Discord")
                    return True

            logger.info("No existing server configs found in Discord")
            self._loaded = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load configs from Discord: {e}")
            return False

    def get_module_description(self, module: FeatureModule) -> str:
        """Get human-readable description of a module"""
        descriptions = {
            FeatureModule.CORE: "🤖 **Core** - Harry's personality, general AI chat, bot management",
            FeatureModule.CFB_DATA: "🏈 **CFB Data** - Player lookup, rankings, matchups, schedules, draft, transfers, betting, ratings",
            FeatureModule.LEAGUE: "🏆 **League** - Timer, advance, charter, rules, league staff, dynasty features",
        }
        return descriptions.get(module, str(module))

    def auto_responses_enabled(self, guild_id: int) -> bool:
        """Check if automatic jump-in responses are enabled (team banter, etc.)"""
        return self.get_setting(guild_id, "auto_responses", True)

    def get_personality_prompt(self, guild_id: int) -> str:
        """Get Harry's personality prompt - ALWAYS the full cockney asshole Duck-hater"""
        return HARRY_PERSONALITY


# Singleton instance
server_config = ServerConfigManager()
