#!/usr/bin/env python3
"""
CFB 26 League Bot - Cog-Based Architecture

This is the new modular entry point that loads Discord.py Cogs.
Each cog handles a specific domain of commands.

Cogs loaded:
- CoreCog: /help, /version, /changelog, /whats_new, /tokens
- AIChatCog: /harry, /ask, /summarize
- RecruitingCog: /recruiting group (7 commands)
- CFBDataCog: /cfb group (9 commands)
- HSStatsCog: /hs group (2 commands)
- LeagueCog: /league group (19 commands)
- CharterCog: /charter group (10 commands)
- AdminCog: /admin group (10 commands)
"""

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CFB26Bot')

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None  # We use /help from CoreCog
)

# Import utilities after bot setup to avoid circular imports
from .utils.server_config import server_config

# ==================== COG LOADING ====================

COG_EXTENSIONS = [
    'cfb_bot.cogs.core',
    'cfb_bot.cogs.ai_chat',
    'cfb_bot.cogs.recruiting',
    'cfb_bot.cogs.cfb_data',
    'cfb_bot.cogs.hs_stats',
    'cfb_bot.cogs.league',
    'cfb_bot.cogs.charter',
    'cfb_bot.cogs.admin',
]


async def load_cogs():
    """Load all cog extensions"""
    for extension in COG_EXTENSIONS:
        try:
            await bot.load_extension(extension)
            logger.info(f"✅ Loaded cog: {extension}")
        except Exception as e:
            logger.error(f"❌ Failed to load cog {extension}: {e}", exc_info=True)


# Global references for dependencies (set in on_ready)
timekeeper_manager = None
charter_editor = None
version_manager = None


async def setup_dependencies():
    """
    Set up dependencies for cogs that need them.
    This is called after bot is ready so we can access Discord objects.
    """
    global timekeeper_manager, charter_editor, version_manager

    logger.info("⚙️ Setting up cog dependencies...")

    # Import optional dependencies
    ai_assistant = None
    AI_AVAILABLE = False
    channel_summarizer = None
    admin_manager = None
    channel_manager = None
    schedule_manager = None

    try:
        from .utils.ai_assistant import ai_assistant as _ai, AI_AVAILABLE as _ai_avail
        ai_assistant = _ai
        AI_AVAILABLE = _ai_avail
        logger.info("✅ AI assistant available")
    except ImportError:
        logger.warning("⚠️ AI assistant not available")

    try:
        from .utils.charter_editor import CharterEditor
        charter_editor = CharterEditor(ai_assistant if AI_AVAILABLE else None, bot=bot)
        # Load charter from Discord
        await charter_editor.load_from_discord()
        logger.info("✅ Charter editor initialized and loaded from Discord")
    except ImportError:
        logger.warning("⚠️ Charter editor not available")

    try:
        from .utils.channel_summarizer import ChannelSummarizer
        channel_summarizer = ChannelSummarizer(ai_assistant if AI_AVAILABLE else None)
        logger.info("✅ Channel summarizer initialized")
    except ImportError:
        logger.warning("⚠️ Channel summarizer not available")

    try:
        from .utils.admin_check import AdminManager
        admin_manager = AdminManager()
        logger.info(f"✅ Admin manager initialized ({admin_manager.get_admin_count()} admins)")
    except ImportError as e:
        logger.warning(f"⚠️ Admin manager not available: {e}")

    try:
        from .utils.channel_manager import ChannelManager
        channel_manager = ChannelManager()
        logger.info("✅ Channel manager initialized")
    except ImportError:
        logger.warning("⚠️ Channel manager not available")

    try:
        from .utils.timekeeper import TimekeeperManager
        timekeeper_manager = TimekeeperManager(bot)
        logger.info("⏰ Timekeeper manager initialized")
        # IMPORTANT: Load saved timer state from Discord
        try:
            await timekeeper_manager.load_saved_state()
            logger.info("✅ Timer state loaded from Discord")
        except Exception as e:
            logger.error(f"❌ Failed to load timer state: {e}")
    except ImportError:
        logger.warning("⚠️ Timekeeper not available")

    try:
        from .utils.schedule_manager import ScheduleManager
        schedule_manager = ScheduleManager()
        logger.info(f"✅ Schedule manager initialized ({len(schedule_manager.teams)} teams)")
    except ImportError:
        logger.warning("⚠️ Schedule manager not available")

    try:
        from .utils.version_manager import VersionManager
        version_manager = VersionManager()
        logger.info("✅ Version manager initialized")
    except ImportError:
        logger.warning("⚠️ Version manager not available")

    # Set dependencies on cogs
    for cog_name, cog in bot.cogs.items():
        if hasattr(cog, 'set_dependencies'):
            if cog_name == 'CoreCog':
                cog.set_dependencies(ai_assistant=ai_assistant, AI_AVAILABLE=AI_AVAILABLE)
            elif cog_name == 'AIChatCog':
                cog.set_dependencies(ai_assistant=ai_assistant, channel_summarizer=channel_summarizer, AI_AVAILABLE=AI_AVAILABLE)
            elif cog_name == 'CharterCog':
                cog.set_dependencies(charter_editor=charter_editor, channel_summarizer=channel_summarizer, ai_assistant=ai_assistant, admin_manager=admin_manager)
            elif cog_name == 'LeagueCog':
                cog.set_dependencies(timekeeper_manager=timekeeper_manager, admin_manager=admin_manager, schedule_manager=schedule_manager, channel_summarizer=channel_summarizer, ai_assistant=ai_assistant, AI_AVAILABLE=AI_AVAILABLE)
            elif cog_name == 'AdminCog':
                cog.set_dependencies(admin_manager=admin_manager, channel_manager=channel_manager, timekeeper_manager=timekeeper_manager)
            elif cog_name == 'RecruitingCog':
                if hasattr(cog, 'admin_manager'):
                    cog.admin_manager = admin_manager
            logger.info(f"  ✓ Dependencies set for {cog_name}")

    logger.info("✅ All dependencies configured")


# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f"🏈 {bot.user} is online!")
    logger.info(f"📊 Connected to {len(bot.guilds)} server(s)")

    # Initialize server config with bot (needed for Discord storage)
    server_config.set_bot(bot)
    await server_config.load_from_discord()
    logger.info(f"⚙️ Server config loaded ({len(server_config._configs)} servers)")

    # Setup dependencies (includes loading timer state, charter, etc.)
    await setup_dependencies()

    # Sync commands to guilds (instant) and globally
    try:
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"✅ Synced {len(synced)} command(s) to {guild.name}")

        # Global sync (takes up to 1 hour for other servers)
        global_synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(global_synced)} command(s) globally")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

    # Send startup notification to admin channels
    await send_startup_notification()


async def send_startup_notification():
    """Send detailed startup status to development channel only"""
    from .utils.server_config import FeatureModule
    from datetime import datetime
    
    # ONLY send to dev channel
    DEV_SERVER_ID = 780882032867803168
    DEV_CHANNEL_ID = 1417732043936108564
    
    dev_channel = bot.get_channel(DEV_CHANNEL_ID)
    if not dev_channel:
        logger.warning(f"⚠️ Could not find dev channel {DEV_CHANNEL_ID}")
        return
    
    # Get version info
    current_version = "3.0.0"
    version_title = "Cog Architecture"
    version_emoji = "🏗️"
    
    if version_manager:
        try:
            current_version = version_manager.get_current_version()
            version_info = version_manager.get_latest_version_info()
            version_title = version_info.get('title', 'Update')
            version_emoji = version_info.get('emoji', '📌')
        except Exception:
            pass
    
    # Build detailed status
    embed = discord.Embed(
        title="🏈 Harry is Online!",
        description=f"**Version {current_version}** - {version_title} {version_emoji}\n"
                   f"**Status:** Deployed ✅ | **Time:** {datetime.now().strftime('%I:%M:%S %p')}\n",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    
    # 📊 Connected Servers
    server_list = []
    for guild in bot.guilds:
        server_list.append(f"• **{guild.name}** (ID: {guild.id}) - {guild.member_count} members")
    
    embed.add_field(
        name=f"📊 Connected Servers ({len(bot.guilds)})",
        value="\n".join(server_list) if server_list else "None",
        inline=False
    )
    
    # ⚙️ Command Sync Status
    sync_status = []
    for guild in bot.guilds:
        sync_status.append(f"• **{guild.name}**: Synced ✅")
    
    embed.add_field(
        name="⚙️ Command Sync Status",
        value="\n".join(sync_status) if sync_status else "None",
        inline=False
    )
    
    # 📦 Loaded Cogs
    cog_list = []
    for cog_name in bot.cogs.keys():
        cog_list.append(f"• {cog_name}")
    
    embed.add_field(
        name=f"📦 Loaded Cogs ({len(bot.cogs)})",
        value="\n".join(cog_list) if cog_list else "None",
        inline=False
    )
    
    # 🔧 Module Status per Server
    module_status = []
    for guild in bot.guilds:
        modules = []
        for module in FeatureModule:
            if server_config.is_module_enabled(guild.id, module):
                modules.append(module.value)
        module_status.append(f"**{guild.name}**: {', '.join(modules) if modules else 'None'}")
    
    embed.add_field(
        name="🔧 Enabled Modules per Server",
        value="\n".join(module_status) if module_status else "None",
        inline=False
    )
    
    # ⏰ Timer Status
    if timekeeper_manager:
        try:
            timer_info = timekeeper_manager.get_restored_timer_info()
            if timer_info:
                timer_channel_id = timer_info.get('channel_id')
                guild_name = timer_info.get('guild_name', 'Unknown')
                guild_id = timer_info.get('guild_id', 'Unknown')
                season = timer_info.get('season', '?')
                week = timer_info.get('week', '?')
                
                timer_text = (
                    f"**✅ Timer Restored Successfully**\n"
                    f"• Server: **{guild_name}** (ID: {guild_id})\n"
                    f"• Channel: #{timer_info['channel_name']} (ID: {timer_channel_id})\n"
                    f"• Season/Week: **Season {season}, Week {week}**\n"
                    f"• Time Remaining: {int(timer_info['hours_remaining'])}h {timer_info['minutes_remaining']}m\n"
                    f"• Ends At: {timer_info['end_time']}"
                )
                embed.add_field(
                    name="⏰ League Timer",
                    value=timer_text,
                    inline=False
                )
                logger.info(f"📊 Timer restored: {guild_name} (ID: {guild_id}) - S{season}W{week}")
            else:
                embed.add_field(
                    name="⏰ League Timer",
                    value="No active timer",
                    inline=False
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not get timer info: {e}")
    
    embed.set_footer(text="Harry Development Status 🛠️ | This message only appears in dev channel")
    
    try:
        await dev_channel.send(embed=embed)
        logger.info(f"📢 Sent detailed startup status to dev channel")
    except Exception as e:
        logger.warning(f"⚠️ Could not send startup to dev channel: {e}")


@bot.event
async def on_guild_join(guild):
    """Called when the bot joins a new guild"""
    logger.info(f"🎉 Joined new guild: {guild.name} (ID: {guild.id})")

    # Sync commands to new guild
    try:
        synced = await bot.tree.sync(guild=guild)
        logger.info(f"✅ Synced {len(synced)} command(s) to {guild.name}")
    except Exception as e:
        logger.error(f"❌ Failed to sync to {guild.name}: {e}")


@bot.event
async def on_message(message):
    """Handle messages - for @mentions and rivalry responses"""
    # Ignore bot messages
    if message.author.bot:
        return

    # Let cogs handle their own message processing
    await bot.process_commands(message)

    # @mention handling is done in AIChatCog
    # Rivalry responses are also handled there


# ==================== MAIN ====================

async def main():
    """Main entry point"""
    # Get token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("❌ DISCORD_BOT_TOKEN environment variable not set!")
        sys.exit(1)

    # Load cogs
    async with bot:
        await load_cogs()
        await bot.start(token)


def run():
    """Run the bot"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot shutting down...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
