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


async def setup_dependencies():
    """
    Set up dependencies for cogs that need them.
    This is called after bot is ready so we can access Discord objects.
    """
    logger.info("⚙️ Setting up cog dependencies...")
    
    # Import optional dependencies
    ai_assistant = None
    AI_AVAILABLE = False
    charter_editor = None
    channel_summarizer = None
    admin_manager = None
    channel_manager = None
    timekeeper_manager = None
    schedule_manager = None
    
    try:
        from .utils.ai_assistant import ai_assistant as _ai, AI_AVAILABLE as _ai_avail
        ai_assistant = _ai
        AI_AVAILABLE = _ai_avail
    except ImportError:
        logger.warning("⚠️ AI assistant not available")
    
    try:
        from .utils.charter_editor import CharterEditor
        charter_editor = CharterEditor()
    except ImportError:
        logger.warning("⚠️ Charter editor not available")
    
    try:
        from .utils.channel_summarizer import ChannelSummarizer
        channel_summarizer = ChannelSummarizer()
    except ImportError:
        logger.warning("⚠️ Channel summarizer not available")
    
    try:
        from .utils.admin_manager import AdminManager
        admin_manager = AdminManager()
    except ImportError:
        logger.warning("⚠️ Admin manager not available")
    
    try:
        from .utils.channel_manager import ChannelManager
        channel_manager = ChannelManager()
    except ImportError:
        logger.warning("⚠️ Channel manager not available")
    
    try:
        from .utils.timekeeper import TimekeeperManager
        timekeeper_manager = TimekeeperManager(bot)
    except ImportError:
        logger.warning("⚠️ Timekeeper not available")
    
    try:
        from .utils.schedule_manager import ScheduleManager
        schedule_manager = ScheduleManager()
    except ImportError:
        logger.warning("⚠️ Schedule manager not available")
    
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
    
    # Setup dependencies
    await setup_dependencies()
    
    # Sync commands
    try:
        for guild in bot.guilds:
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"✅ Synced {len(synced)} command(s) to {guild.name}")
        
        # Global sync
        global_synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(global_synced)} command(s) globally")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")
    
    # Send startup notification to admin channels
    for guild in bot.guilds:
        admin_channel_id = server_config.get_admin_channel(guild.id)
        if admin_channel_id:
            channel = guild.get_channel(admin_channel_id)
            if channel:
                try:
                    embed = discord.Embed(
                        title="🏈 Harry is Online!",
                        description="Right then, I'm up and running with the new cog architecture!",
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="📦 Loaded Cogs",
                        value=", ".join(bot.cogs.keys()),
                        inline=False
                    )
                    embed.set_footer(text="Harry's CFB Bot 🏈 | Refactored!")
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.warning(f"⚠️ Could not send startup notification: {e}")


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
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("❌ DISCORD_TOKEN environment variable not set!")
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

