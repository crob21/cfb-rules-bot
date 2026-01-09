#!/usr/bin/env python3
# =============================================================================
# CRITICAL: audioop fix MUST be imported before discord!
# Python 3.13 removed audioop module which discord.py needs.
# DO NOT MOVE THIS IMPORT - IT MUST BE BEFORE DISCORD!
# =============================================================================
from cfb_bot.utils import audioop_fix  # noqa: E402, I001, I002 isort:skip
"""
CFB 26 League Bot - A Discord bot for the CFB 26 online dynasty league

This bot provides AI-powered assistance for league members, including:
- Natural language processing for league questions
- Slash commands for quick access to rules and information
- Rivalry responses and fun interactions
- Integration with the official league charter

Author: CFB 26 League
License: MIT
Version: 1.0.0
"""
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Admin-only channel for bot notifications (Booze's Playground)
ADMIN_CHANNEL_ID = 1417663211292852244

# Default notification channel for timer announcements (can be changed with /set_timer_channel)
# This is the fallback - the persisted value from timekeeper takes precedence
DEFAULT_NOTIFICATION_CHANNEL_ID = 1261662233109205146  # #general
GENERAL_CHANNEL_ID = DEFAULT_NOTIFICATION_CHANNEL_ID  # Will be updated on startup from saved settings


def get_notification_channel():
    """Get the notification channel, using timekeeper's saved value if available"""
    if timekeeper_manager:
        channel_id = timekeeper_manager.get_notification_channel_id()
    else:
        channel_id = GENERAL_CHANNEL_ID
    return bot.get_channel(channel_id)


async def send_week_schedule(channel, week_num):
    """Send the schedule for a given week to a channel"""
    if week_num is None:
        return

    # Only show schedule for regular season weeks (0-13)
    if week_num > 13:
        logger.info(f"📅 Week {week_num} is not regular season, skipping schedule")
        return

    try:
        schedule_mgr = get_schedule_manager()
        if not schedule_mgr:
            return

        week_data = schedule_mgr.get_week_schedule(week_num)
        if not week_data:
            logger.warning(f"⚠️ No schedule data for Week {week_num}")
            return

        # Build the schedule embed
        schedule_embed = discord.Embed(
            title=f"📅 Week {week_num} Matchups",
            description="Here's what's on the slate this week, ya muppets!",
            color=0x00ff00
        )

        # Bye teams (bold user teams)
        bye_teams = week_data.get('bye_teams', [])
        if bye_teams:
            schedule_embed.add_field(
                name="🛋️ Bye Week",
                value=schedule_mgr.format_bye_teams(bye_teams),
                inline=False
            )

        # Games (bold user teams)
        games = week_data.get('games', [])
        if games:
            games_text = "\n".join([schedule_mgr.format_game(g) for g in games])
            schedule_embed.add_field(
                name="🎮 This Week's Games",
                value=games_text,
                inline=False
            )

        schedule_embed.set_footer(text="Harry's Schedule Tracker 🏈 | Get your games done!")
        await channel.send(embed=schedule_embed)
        logger.info(f"📅 Sent Week {week_num} schedule")

    except Exception as e:
        logger.error(f"❌ Failed to send schedule: {e}")


from .utils import \
    timekeeper as timekeeper_module  # For updating NOTIFICATION_CHANNEL_ID
from .utils.admin_check import AdminManager
from .utils.channel_manager import ChannelManager
from .utils.charter_editor import CharterEditor
from .utils.schedule_manager import ScheduleManager, get_schedule_manager
from .utils.summarizer import ChannelSummarizer
# Import timekeeper, summarizer, charter editor, admin manager, version manager, and channel manager
from .utils.timekeeper import (CFB_DYNASTY_WEEKS, TOTAL_WEEKS_PER_SEASON,
                               TimekeeperManager, format_est_time,
                               get_week_actions, get_week_info, get_week_name,
                               get_week_notes, get_week_phase)
from .utils.version_manager import VersionManager
from .utils.player_lookup import player_lookup
from .utils.server_config import server_config, FeatureModule


async def check_module_enabled(interaction, module) -> bool:
    """
    Check if a module is enabled for this server.
    Returns True if enabled, False if disabled (and sends error message).
    """
    if not interaction.guild:
        return True  # Allow in DMs

    if server_config.is_module_enabled(interaction.guild.id, module):
        return True

    # Module is disabled - send helpful message
    module_names = {
        FeatureModule.CFB_DATA: "CFB Data",
        FeatureModule.LEAGUE: "League Features",
    }
    name = module_names.get(module, module.value)

    await interaction.response.send_message(
        f"❌ **{name}** module is not enabled on this server.\n"
        f"An admin can enable it with: `/config enable {module.value}`",
        ephemeral=True
    )
    return False


# Optional Google Docs integration
try:
    from google_docs_integration import GoogleDocsIntegration
    GOOGLE_DOCS_AVAILABLE = True
except ImportError:
    GOOGLE_DOCS_AVAILABLE = False

# Optional AI integration
try:
    from .ai.ai_integration import AICharterAssistant

    # Check if at least one AI API key is available
    AI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
except ImportError:
    AI_AVAILABLE = False

# Load environment variables
load_dotenv()

# League-related keywords for classification
LEAGUE_KEYWORDS = [
    'rules', 'charter'
]

def classify_question(question: str) -> tuple[bool, bool, list[str]]:
    """Classify a question and return (is_question, league_related, matched_keywords)"""
    is_question = question.strip().endswith('?')
    league_related = any(f' {keyword} ' in f' {question.lower()} ' for keyword in LEAGUE_KEYWORDS)
    matched_keywords = [kw for kw in LEAGUE_KEYWORDS if f' {kw} ' in f' {question.lower()} '] if league_related else []
    return is_question, league_related, matched_keywords

# Set up comprehensive logging
def setup_logging():
    """
    Set up comprehensive logging for Render deployment.

    Configures logging to both file and console output with proper formatting.
    Creates logs directory if it doesn't exist.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set Discord.py logging level
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)

    # Set our bot logger
    bot_logger = logging.getLogger('CFB26Bot')
    bot_logger.setLevel(logging.INFO)

    return bot_logger

# Initialize logging
logger = setup_logging()

# Bot configuration
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True  # Required to read message content

bot = commands.Bot(command_prefix='!', intents=intents)

# Background task to clean up expired pending requests
@tasks.loop(minutes=5)
async def cleanup_expired_pending():
    """Clean up expired pending charter updates and rule scans"""
    now = datetime.now().timestamp()

    # Clean up pending charter updates
    if hasattr(bot, 'pending_charter_updates'):
        expired = [msg_id for msg_id, data in bot.pending_charter_updates.items()
                   if now > data.get("expires", 0)]
        for msg_id in expired:
            del bot.pending_charter_updates[msg_id]
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired charter update(s)")

    # Clean up pending rule scans
    if hasattr(bot, 'pending_rule_scans'):
        expired = [msg_id for msg_id, data in bot.pending_rule_scans.items()
                   if now > data.get("expires", 0)]
        for msg_id in expired:
            del bot.pending_rule_scans[msg_id]
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired rule scan(s)")

    # Clean up old processed messages (keep last 1000)
    global processed_messages
    if len(processed_messages) > 1000:
        # Convert to list, keep last 1000, convert back to set
        processed_messages = set(list(processed_messages)[-1000:])
        logger.info("🧹 Trimmed processed_messages set")

@cleanup_expired_pending.before_loop
async def before_cleanup():
    await bot.wait_until_ready()

# Initialize Google Docs integration if available
google_docs = None
if GOOGLE_DOCS_AVAILABLE:
    google_docs = GoogleDocsIntegration()

# Initialize AI integration if available
ai_assistant = None
if AI_AVAILABLE:
    ai_assistant = AICharterAssistant()

# Initialize timekeeper manager, summarizer, charter editor, admin manager, version manager, and channel manager
timekeeper_manager = None
channel_summarizer = None
charter_editor = None
admin_manager = None
version_manager = None
channel_manager = None
schedule_manager = None

# Simple rate limiting to prevent duplicate responses
last_message_time = {}
processed_messages = set()  # Track processed message IDs
processed_content = set()  # Track processed content+author combinations
recent_content_times = {}  # Track content + timestamp for time-based deduplication
processing_lock = asyncio.Lock()  # Lock for atomic message processing checks

@bot.event
async def on_ready():
    """
    Called when the bot is ready and connected to Discord.

    Performs initial setup including:
    - Loading league data
    - Syncing slash commands
    - Logging connection status
    """
    global timekeeper_manager, channel_summarizer, charter_editor, admin_manager, version_manager, channel_manager, schedule_manager

    try:
        # Initialize version manager first to get version
        version_manager = VersionManager()
        current_version = version_manager.get_current_version()

        logger.info(f'🏈 CFB 26 League Bot ({bot.user}) v{current_version} has connected to Discord!')
        logger.info(f'🔗 Bot ID: {bot.user.id}')
        logger.info(f'📛 Bot Username: {bot.user.name}')
        logger.info(f'🏷️ Bot Display Name: {bot.user.display_name}')
        logger.info(f'📊 Connected to {len(bot.guilds)} guilds')
        logger.info(f'👋 Harry is ready to help with league questions!')

        # Start cleanup task
        if not cleanup_expired_pending.is_running():
            cleanup_expired_pending.start()
            logger.info('🧹 Started cleanup task for expired pending requests')

        # Initialize channel manager
        channel_manager = ChannelManager()
        logger.info(f'🔇 Channel manager initialized ({channel_manager.get_blocked_count()} blocked channels)')

        # Initialize admin manager
        admin_manager = AdminManager()
        logger.info(f'🔐 Admin manager initialized ({admin_manager.get_admin_count()} admin(s) configured)')

        # Initialize timekeeper manager
        timekeeper_manager = TimekeeperManager(bot)
        logger.info('⏰ Timekeeper manager initialized')

        # Restore any saved timer state (wrap in try/except to prevent crashes)
        try:
            await timekeeper_manager.load_saved_state()
        except Exception as e:
            logger.error(f"❌ Failed to load saved timer state: {e}")
            logger.exception("Full error details:")
            # Don't crash - bot can still work without restored timers

        # Initialize channel summarizer (with AI if available)
        channel_summarizer = ChannelSummarizer(ai_assistant if AI_AVAILABLE else None)
        logger.info('📊 Channel summarizer initialized')

        # Initialize charter editor (with AI if available and bot for Discord persistence)
        charter_editor = CharterEditor(ai_assistant if AI_AVAILABLE else None, bot=bot)
        logger.info('📝 Charter editor initialized')

        # Load charter from Discord (persisted across deployments)
        discord_charter = await charter_editor.load_from_discord()
        if discord_charter:
            logger.info('📜 Charter loaded from Discord persistence')
        else:
            logger.info('📜 Using charter from file (no Discord version found)')

        # Initialize server config manager
        server_config.set_bot(bot)
        await server_config.load_from_discord()
        logger.info(f'⚙️ Server config manager initialized ({len(server_config._configs)} server configs loaded)')

        # Initialize schedule manager
        schedule_manager = get_schedule_manager()
        logger.info(f'📅 Schedule manager initialized ({len(schedule_manager.teams)} teams)')

        # Load league data
        await load_league_data()

        # Sync slash commands
        try:
            # Sync to specific guilds for instant command updates (5 seconds instead of 1 hour!)
            guild_ids = [
                1261662233109205144,  # Main server
                780882032867803168,   # Second server
            ]

            # Sync to each guild (instant)
            for guild_id in guild_ids:
                guild = discord.Object(id=guild_id)
                bot.tree.copy_global_to(guild=guild)
                synced_guild = await bot.tree.sync(guild=guild)
                logger.info(f'✅ Synced {len(synced_guild)} command(s) to guild {guild_id} (instant!)')

            # Also sync globally for other servers (takes up to 1 hour)
            synced_global = await bot.tree.sync()
            logger.info(f'✅ Synced {len(synced_global)} command(s) globally (may take up to 1 hour)')

            logger.info(f'🎯 Try: /harry what are the league rules?')
            logger.info(f'💬 Or mention @Harry in chat for natural conversations!')
        except Exception as e:
            logger.error(f'❌ Failed to sync commands: {e}')
    except Exception as e:
        logger.error(f"❌ Critical error in on_ready: {e}")
        logger.exception("Full error details:")
        # Don't re-raise - let bot continue running
        # The bot will still connect, just without some features

@bot.event
async def on_message(message):
    """
    Handle regular chat messages and provide intelligent responses.

    Processes messages for:
    - Bot mentions
    - League-related keywords
    - Direct questions
    - Greetings
    - Rivalry responses

    Args:
        message (discord.Message): The message received
    """
    # PRIORITY CHECK: Don't deduplicate @everyone/@here + "advanced" messages (important trigger)
    is_advance_trigger = False
    if message.mention_everyone or (message.role_mentions and len(message.role_mentions) > 0):
        message_lower = message.content.lower()
        if 'advanced' in message_lower:
            is_advance_trigger = True
            logger.info(f"🔥 Detected advance trigger - bypassing deduplication")

    # Prevent duplicate processing of the same message (check first!)
    # Use atomic check-and-add with lock to prevent race conditions
    if not is_advance_trigger:  # Skip deduplication for advance triggers
        global recent_content_times, processing_lock
        content_key = f"{message.author.id}:{message.content}:{message.channel.id}"
        current_time = asyncio.get_event_loop().time()

        # Use lock to make check-and-add atomic
        async with processing_lock:
            # ATOMIC: Check and add message ID immediately to prevent race conditions
            # If it's already in the set, another handler is processing it
            if message.id in processed_messages:
                logger.info(f"⏭️ Skipping duplicate message ID: {message.id}")
                return

            # Add message ID FIRST before any other checks (atomic operation)
            processed_messages.add(message.id)

            # Now check content-based deduplication
            if content_key in processed_content:
                logger.info(f"⏭️ Skipping duplicate content: {content_key[:50]}...")
                return

            # Time-based deduplication: check if same content was processed in last 2 seconds
            if content_key in recent_content_times:
                time_diff = current_time - recent_content_times[content_key]
                if time_diff < 2.0:  # Within 2 seconds
                    logger.info(f"⏭️ Skipping duplicate content (time-based): {content_key[:50]}... (seen {time_diff:.2f}s ago, msg_id={message.id})")
                    return

            # Add to content tracking sets
            processed_content.add(content_key)
            recent_content_times[content_key] = current_time

        # Clean up old entries from recent_content_times (keep last 100 entries)
        if len(recent_content_times) > 100:
            # Remove entries older than 10 seconds
            cutoff_time = current_time - 10.0
            # Filter in place by rebuilding the dict
            keys_to_remove = [k for k, v in recent_content_times.items() if v <= cutoff_time]
            for key in keys_to_remove:
                del recent_content_times[key]

        logger.debug(f"✅ Processing new message: ID={message.id}, Content={content_key[:50]}...")
    else:
        # For advance triggers, just log that we're processing it
        logger.info(f"⚡ Processing advance trigger message: ID={message.id}, from {message.author}")

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if Harry is enabled in this channel (channel whitelist)
    if message.guild:
        channel_id = message.channel.id
        guild_id = message.guild.id
        if not server_config.is_channel_enabled(guild_id, channel_id):
            # Harry is not enabled in this channel - stay silent
            logger.debug(f"🔇 Channel {channel_id} not enabled for Harry in guild {guild_id}")
            return

    # Check if the bot is @mentioned (only responds to @CFB Bot, not just "harry" in text)
    bot_mentioned = False
    if message.mentions:
        for mention in message.mentions:
            if mention.id == bot.user.id:
                bot_mentioned = True
                break

    # PRIORITY: Check for @everyone/@here + "advanced" to restart timer
    # Available to everyone - no admin check needed
    if message.mention_everyone or (message.role_mentions and len(message.role_mentions) > 0):
        # Check if message contains "advanced" (case-insensitive)
        message_lower = message.content.lower()
        if 'advanced' in message_lower:
            logger.info(f"🔄 @everyone/@channel + 'advanced' detected from {message.author} - restarting timer")

            if not timekeeper_manager:
                logger.warning("⚠️ Timekeeper manager not available for restart")
            else:
                # Stop current timer (if exists)
                await timekeeper_manager.stop_timer(message.channel)

                # Increment the week (manual advance)
                season_info = timekeeper_manager.get_season_week()
                if season_info['season'] and season_info['week'] is not None:
                    old_week = season_info['week']
                    old_week_name = season_info.get('week_name', f"Week {old_week}")
                    await timekeeper_manager.increment_week()
                    # Refresh season_info after increment
                    season_info = timekeeper_manager.get_season_week()
                    new_week_name = season_info.get('week_name', f"Week {season_info['week']}")
                    logger.info(f"📅 Manual advance: {old_week_name} → {new_week_name}")

                # Start new timer (default 48 hours)
                success = await timekeeper_manager.start_timer(message.channel, 48)

                if success:
                    # Get season/week info for display (already refreshed above if incremented)
                    if not season_info:
                        season_info = timekeeper_manager.get_season_week()
                    if season_info['season'] and season_info['week'] is not None:
                        week_name = season_info.get('week_name', f"Week {season_info['week']}")
                        next_week_name = get_week_name(season_info['week'] + 1)
                        phase = season_info.get('phase', 'Regular Season')
                        season_text = f"**Season {season_info['season']}**\n📍 {week_name} → **{next_week_name}**\n🏈 Phase: {phase}\n\n"
                    else:
                        season_text = ""

                    embed = discord.Embed(
                        title="⏰ Advance Countdown Restarted!",
                        description=f"Right then! Timer's been restarted!\n\n🏈 **48 HOUR COUNTDOWN STARTED** 🏈\n\n{season_text}You got **48 hours** to get your bleedin' games done!\n\nI'll be remindin' you lot at:\n• 24 hours remaining\n• 12 hours remaining\n• 6 hours remaining\n• 1 hour remaining\n\nAnd when time's up... well, you'll know! 😈",
                        color=0x00ff00
                    )
                    status = timekeeper_manager.get_status(message.channel)
                    embed.add_field(
                        name="⏳ Deadline",
                        value=format_est_time(status['end_time'], '%A, %B %d at %I:%M %p'),
                        inline=False
                    )
                    embed.set_footer(text="Harry's Advance Timer 🏈 | Use /time_status to check progress")
                    # Send to notification channel (#general)
                    notification_channel = get_notification_channel()
                    if notification_channel:
                        await notification_channel.send(content="@everyone", embed=embed)
                        logger.info(f"⏰ Timer restarted by {message.author} via @everyone + 'advanced' - announced in #{notification_channel.name}")

                        # Send schedule for the new week
                        await send_week_schedule(notification_channel, season_info.get('week') if season_info else None)
                    else:
                        await message.channel.send(content="@everyone", embed=embed)
                        logger.warning(f"⚠️ #general not found, announced in {message.channel}")
                else:
                    embed = discord.Embed(
                        title="❌ Failed to Restart Timer",
                        description="Couldn't restart the timer, mate. Try using `/advance` instead!",
                        color=0xff0000
                    )
                    await message.channel.send(embed=embed)
                    logger.error(f"❌ Failed to restart timer for {message.author}")

            # Don't process this message further - timer restart was handled
            return

    # Check if unprompted responses are allowed in this channel
    channel_allows_unprompted = True
    if channel_manager:
        channel_allows_unprompted = channel_manager.can_respond_unprompted(message.channel.id)

    # If bot is mentioned, ALWAYS respond (works in any channel)
    # If bot is NOT mentioned, only respond if channel allows unprompted responses
    if not bot_mentioned and not channel_allows_unprompted:
        return

    # Comprehensive logging (only after deduplication and channel checks)
    guild_name = message.guild.name if message.guild else "DM"
    logger.info(f"📨 Message received: '{message.content}' from {message.author} in #{message.channel} (Server: {guild_name})")
    logger.info(f"📊 Message details: length={len(message.content)}, type={type(message.content)}, repr={repr(message.content)}")
    logger.info(f"🔍 DEBUG: Starting message processing for: '{message.content}'")
    logger.info(f"🔍 Channel check: current='{message.channel.name}' (ID: {message.channel.id}), bot_mentioned={bot_mentioned}, unprompted_allowed={channel_allows_unprompted}")

    # Skip empty messages
    if not message.content or message.content.strip() == '':
        logger.info(f"⏭️ Skipping empty message from {message.author}")
        return

    # Simple rate limiting to prevent duplicate responses (5 second cooldown per user)
    # Reuse current_time from deduplication check above
    user_id = message.author.id
    if user_id in last_message_time and current_time - last_message_time[user_id] < 5:
        logger.info(f"⏭️ Rate limiting: skipping message from {message.author} (too recent)")
        return
    last_message_time[user_id] = current_time

    # Log mention info (bot_mentioned already set above)
    if message.mentions:
        for mention in message.mentions:
            logger.info(f"🔍 Mention found: {mention} (ID: {mention.id}) vs bot ID: {bot.user.id}")
            if mention.id == bot.user.id:
                break  # Already set bot_mentioned above

    # Very specific rule-related phrases that indicate actual questions about league rules
    rule_keywords = [
        'what are the rules', 'league rules', 'recruiting rules', 'transfer rules', 'charter rules',
        'league policy', 'recruiting policy', 'transfer policy', 'penalty rules', 'difficulty rules',
        'sim rules', 'what are the league rules', 'how do the rules work', 'explain the rules',
        'tell me about the rules', 'league charter', 'recruiting policy', 'transfer policy'
    ]
    contains_keywords = any(keyword in message.content.lower() for keyword in rule_keywords)
    is_question = message.content.strip().endswith('?')

    # Debug: show which keyword was matched
    matched_keywords = [keyword for keyword in rule_keywords if keyword in message.content.lower()]
    if matched_keywords:
        logger.info(f"🔍 Matched rule keywords: {matched_keywords}")

    logger.info(f"🔍 Message analysis: bot_mentioned={bot_mentioned}, contains_keywords={contains_keywords}, is_question={is_question}")

    # Check for greetings (only when bot is @mentioned)
    greetings = ['hi', 'hello', 'hey']
    is_greeting = bot_mentioned and any(greeting in message.content.lower() for greeting in greetings)

    # Check for auto jump-in responses (gated by auto_responses setting)
    guild_id = message.guild.id if message.guild else 0
    channel_id = message.channel.id if message.channel else 0
    auto_responses = server_config.auto_responses_enabled(guild_id, channel_id)

    # Team banter responses - only if auto_responses is enabled
    team_keywords = {
        'oregon': 'Fuck Oregon! 🦆💩',
        'ducks': 'Ducks are assholes! 🦆💩',
        'oregon ducks': 'Fuck Oregon! 🦆💩',
        'oregon state': 'BEAVS!',
        'detroit lions': 'Go Lions! 🦁',
        'lions': 'Go Lions! 🦁',
        'tampa bay buccaneers': 'Go Bucs! 🏴‍☠️',
        'buccaneers': 'Go Bucs! 🏴‍☠️',
        'bucs': 'Go Bucs! 🏴‍☠️',
        'chicago bears': 'Da Bears! 🧸',
        'bears': 'Da Bears! 🧸',
        'washington': 'Go Huskies! 🐕',
        'huskies': 'Go Huskies! 🐕',
        'uw': 'Go Huskies! 🐕',
        'alabama': 'Roll Tide! 🐘',
        'crimson tide': 'Roll Tide! 🐘',
        'georgia': 'Wrong Dawgs...',
        'bulldogs': 'Wrong Dawgs...',
        'ohio state': 'Ohio sucks! 🌰',
        'buckeyes': 'Ohio sucks! 🌰',
        'michigan': 'Go Blue! 💙',
        'wolverines': 'Go Blue! 💙',
    } if auto_responses else {}

    # Info responses - always available (not gated)
    info_keywords = {
        'rules': 'Here are the CFB 26 league rules! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
        'league rules': 'Here are the CFB 26 league rules! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
        'charter': 'Here\'s the official CFB 26 league charter! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
        'league charter': 'Here\'s the official CFB 26 league charter! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)'
    }

    # Combine both keyword dicts
    all_keywords = {**team_keywords, **info_keywords}

    auto_response = None
    for keyword, response in all_keywords.items():
        if keyword in message.content.lower():
            auto_response = response
            break

    # Don't trigger auto response if it's a clear question (especially with "harry" mentioned)
    if auto_response and (is_question or (bot_mentioned and len(message.content.split()) > 2)):
        auto_response = None
        logger.info(f"🔍 Auto response overridden: question detected or harry mentioned with context")

    logger.info(f"🔍 Response triggers: is_greeting={is_greeting}, auto_response={auto_response is not None}")

    # PRIORITY 1: Handle auto responses immediately (no AI processing needed)
    if auto_response:
        logger.info(f"🏆 Auto response triggered: {auto_response[:50]}...")
        logger.info(f"✅ Bot will respond to message: '{message.content}' (Server: {guild_name})")

        # Don't respond to slash commands
        if message.content.startswith('/'):
            return

        # Add a small delay to make it feel more natural
        await asyncio.sleep(1)

        # Create a friendly response
        embed = discord.Embed(
            title="🏈 Harry's Response",
            color=0x1e90ff
        )
        embed.description = auto_response
        embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")

        # Send the response immediately
        await message.channel.send(embed=embed)
        return

    # PRIORITY 2: Handle direct mentions and league-related questions with AI
    is_question, league_related_question, matched_keywords = classify_question(message.content)

    logger.info(f"🔍 DEBUG: bot_mentioned={bot_mentioned}, is_question={is_question}, league_related_question={league_related_question}")

    # Direct mentions get AI responses regardless of content
    if bot_mentioned or league_related_question:
        # Enhanced classification logging
        classification_reason = []
        if bot_mentioned:
            classification_reason.append("bot_mentioned=True")
        if league_related_question:
            classification_reason.append(f"league_question=True (matched: {matched_keywords})")

        logger.info(f"🎯 CLASSIFICATION: {message.author} ({message.author.id}) - '{message.content}'")
        logger.info(f"🔍 Classification reason: {', '.join(classification_reason)}")
        logger.info(f"💬 Response triggered: bot_mentioned={bot_mentioned}, league_question={league_related_question}")
        logger.info(f"✅ Bot will respond to message: '{message.content}' (Server: {guild_name})")

        # Don't respond to slash commands
        if message.content.startswith('/'):
            return

        # Add a small delay to make it feel more natural
        await asyncio.sleep(1)

        # Create a friendly response
        embed = discord.Embed(
            title="🏈 Harry's Response",
            color=0x1e90ff
        )

        # Handle AI responses
        # Step 0: Check if this is a "tell X to Y" relay request
        if bot_mentioned:
            # Check for "tell <user> [to] <message>" pattern (to is optional)
            # Handles: "tell @user to message" OR "tell @user message"
            tell_pattern = re.search(r'tell\s+<@!?(\d+)>\s+(?:to\s+)?(.+)', message.content, re.IGNORECASE)
            if tell_pattern:
                target_user_id = int(tell_pattern.group(1))
                relay_message = tell_pattern.group(2).strip()

                # Get the target user
                target_user = message.guild.get_member(target_user_id) if message.guild else None
                if target_user:
                    logger.info(f"📨 Relay request: {message.author} wants to tell {target_user} '{relay_message}'")

                    # Send the relay message
                    embed = discord.Embed(
                        title=f"📨 Message from {message.author.display_name}",
                        description=f"Oi {target_user.mention}! {relay_message}",
                        color=0xff9900
                    )
                    embed.set_footer(text=f"Relayed by Harry 🏈")
                    await message.channel.send(embed=embed)
                    logger.info(f"✅ Relay message sent to {target_user}")
                    return  # Don't continue with AI response
                else:
                    logger.warning(f"⚠️ Could not find target user {target_user_id} for relay")
            else:
                logger.debug(f"🔍 No relay pattern matched for: {message.content[:50]}...")

            # Check if this is a commissioner update request
            commish_patterns = [
                (r'update\s+(?:the\s+)?(?:league\s+)?commish(?:ioner)?\s+to\s+(.+)', 1),
                (r'change\s+(?:the\s+)?(?:league\s+)?commish(?:ioner)?\s+to\s+(.+)', 1),
                (r'set\s+(?:the\s+)?(?:league\s+)?commish(?:ioner)?\s+to\s+(.+)', 1),
                (r'make\s+(.+)\s+(?:the\s+)?(?:league\s+)?commish(?:ioner)', 1),
            ]

            new_commish_name = None
            for pattern, group_num in commish_patterns:
                match = re.search(pattern, message.content, re.IGNORECASE)
                if match and match.lastindex >= group_num:
                    new_commish_name = match.group(group_num)
                    break

            if new_commish_name and bot_mentioned and admin_manager and admin_manager.is_admin(message.author, message):
                # Check if charter editor is available
                if not charter_editor:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Charter editor not available",
                        color=0xff0000
                    )
                    await message.channel.send(embed=embed)
                    return

                # Clean up the name (remove @mentions, extra whitespace)
                new_commish_name = new_commish_name.strip()

                # Check if it's a user mention
                mention_match = re.search(r'<@!?(\d+)>', new_commish_name)
                if mention_match:
                    user_id = int(mention_match.group(1))
                    try:
                        target_user = await message.guild.fetch_member(user_id) if message.guild else None
                        if target_user:
                            new_commish_name = target_user.display_name
                    except Exception:
                        pass  # User not found, use raw name

                logger.info(f"👔 Commissioner update requested by {message.author}: {new_commish_name}")

                # Update the commissioner
                result = charter_editor.update_commissioner(new_commish_name)

                if result['success']:
                    embed = discord.Embed(
                        title="✅ Commissioner Updated!",
                        description=f"Right then! I've updated the League Commish to **{new_commish_name}**!\n\nCharter has been updated and backed up automatically.",
                        color=0x00ff00
                    )
                    embed.set_footer(text=f"Updated by {message.author.display_name} 🏈")
                    await message.channel.send(embed=embed)
                    logger.info(f"✅ Commissioner updated to: {new_commish_name}")
                else:
                    embed = discord.Embed(
                        title="❌ Update Failed",
                        description=f"Couldn't update the commissioner, mate!\n\n**Error:** {result['message']}",
                        color=0xff0000
                    )
                    await message.channel.send(embed=embed)
                    logger.error(f"❌ Failed to update commissioner: {result['message']}")

                return  # Don't continue with AI response
            elif new_commish_name and bot_mentioned:
                # User requested update but isn't admin
                embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="You need to be a bot admin to update the commissioner, ya muppet!",
                    color=0xff0000
                )
                await message.channel.send(embed=embed)
                return

            # Check if this is an interactive charter update request
            charter_update_keywords = [
                'update the', 'change the', 'modify the', 'edit the',
                'add a rule', 'add rule', 'new rule', 'remove the', 'delete the',
                'update rule', 'change rule', 'set the'
            ]

            # Check for charter-related update patterns
            message_lower = message.content.lower()
            is_charter_update = (
                bot_mentioned and
                any(keyword in message_lower for keyword in charter_update_keywords) and
                any(term in message_lower for term in ['rule', 'charter', 'policy', 'schedule', 'advance', 'recruiting', 'transfer', 'quarter', 'difficulty', 'setting'])
            )

            if is_charter_update and admin_manager and admin_manager.is_admin(message.author, message):
                if not charter_editor:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Charter editor not available",
                        color=0xff0000
                    )
                    await message.channel.send(embed=embed)
                    return

                if not AI_AVAILABLE or not ai_assistant:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="AI not available for charter updates",
                        color=0xff0000
                    )
                    await message.channel.send(embed=embed)
                    return

                logger.info(f"📝 Charter update request from {message.author}: {message.content}")

                # Show thinking message
                thinking_msg = await message.channel.send("🔧 Analyzing your charter update request...")

                try:
                    # Parse the update request
                    parsed = await charter_editor.parse_update_request(message.content)

                    if not parsed or parsed.get("action") == "unknown":
                        error_msg = parsed.get("error", "I couldn't understand that update request") if parsed else "Failed to parse request"
                        await thinking_msg.edit(content=f"❌ {error_msg}\n\nTry being more specific, like:\n• `update the advance time to 10am`\n• `add a rule: no trading during playoffs`\n• `change quarter length to 5 minutes`")
                        return

                    # Generate preview
                    preview = await charter_editor.generate_update_preview(parsed)

                    if not preview:
                        await thinking_msg.edit(content="❌ Couldn't generate a preview for this change. The section might not exist or the request was unclear.")
                        return

                    # Delete thinking message
                    await thinking_msg.delete()

                    # Show before/after preview
                    embed = discord.Embed(
                        title="📝 Charter Update Preview",
                        description=f"**{parsed.get('summary', 'Proposed change')}**",
                        color=0xffa500
                    )

                    # Truncate long text for display
                    before_text = preview.get("before", "N/A")
                    after_text = preview.get("after", "N/A")

                    if len(before_text) > 500:
                        before_text = before_text[:500] + "..."
                    if len(after_text) > 500:
                        after_text = after_text[:500] + "..."

                    embed.add_field(
                        name="📄 BEFORE",
                        value=f"```\n{before_text}\n```",
                        inline=False
                    )
                    embed.add_field(
                        name="📝 AFTER",
                        value=f"```\n{after_text}\n```",
                        inline=False
                    )
                    embed.add_field(
                        name="⚠️ Confirm Change",
                        value="React with ✅ to apply this change, or ❌ to cancel.\n*This will create an automatic backup.*",
                        inline=False
                    )
                    embed.set_footer(text=f"Requested by {message.author.display_name} | Expires in 60 seconds")

                    preview_msg = await message.channel.send(embed=embed)

                    # Add reaction options
                    await preview_msg.add_reaction("✅")
                    await preview_msg.add_reaction("❌")

                    # Store pending update for reaction handler
                    if not hasattr(bot, 'pending_charter_updates'):
                        bot.pending_charter_updates = {}

                    bot.pending_charter_updates[preview_msg.id] = {
                        "user_id": message.author.id,
                        "user_name": message.author.display_name,
                        "new_charter": preview.get("full_new_charter"),
                        "description": parsed.get("summary"),
                        "before": preview.get("before"),
                        "after": preview.get("after"),
                        "expires": datetime.now().timestamp() + 60  # 60 second timeout
                    }

                    logger.info(f"📝 Charter update preview sent, awaiting confirmation from {message.author}")
                    return

                except Exception as e:
                    logger.error(f"❌ Error processing charter update: {e}", exc_info=True)
                    await thinking_msg.edit(content=f"❌ Error processing update: {str(e)}")
                    return

            elif is_charter_update and bot_mentioned:
                # User requested update but isn't admin
                embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="You need to be a bot admin to update the charter, ya muppet!",
                    color=0xff0000
                )
                await message.channel.send(embed=embed)
                return

            # Check if this is a CFB data query (player, rankings, matchup, etc.)
            if bot_mentioned and player_lookup.is_available:
                message_lower = message.content.lower()

                # Check for bulk player lookup (multiple lines with player names)
                bulk_indicators = ['look up these', 'lookup these', 'find these', 'check these', 'these players', 'player list']
                content_lines = message.content.strip().split('\n')

                # Detect bulk lookup: either explicit request or multiple lines with player-like content
                is_bulk_request = any(ind in message_lower for ind in bulk_indicators)
                has_multiple_players = len(content_lines) >= 3 and any('(' in line for line in content_lines)

                if is_bulk_request or has_multiple_players:
                    # Try to parse as player list
                    player_list = player_lookup.parse_player_list(message.content)

                    if len(player_list) >= 2:
                        logger.info(f"🏈 Bulk player lookup: {len(player_list)} players detected")
                        thinking_msg = await message.channel.send(f"🔍 Looking up {len(player_list)} players, hang on...")

                        try:
                            results = await player_lookup.lookup_multiple_players(player_list)
                            response = player_lookup.format_bulk_player_response(results)

                            await thinking_msg.delete()

                            # Split into multiple messages if too long
                            if len(response) > 4000:
                                # Send as multiple embeds
                                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                                for i, chunk in enumerate(chunks):
                                    embed = discord.Embed(
                                        title="🏈 Player Lookup Results" + (f" (Part {i+1})" if len(chunks) > 1 else ""),
                                        description=chunk,
                                        color=0x1e90ff
                                    )
                                    if i == len(chunks) - 1:
                                        embed.set_footer(text="Harry's Bulk Lookup 🏈 | Data from CollegeFootballData.com")
                                    await message.channel.send(embed=embed)
                            else:
                                embed = discord.Embed(
                                    title="🏈 Player Lookup Results",
                                    description=response,
                                    color=0x1e90ff
                                )
                                embed.set_footer(text="Harry's Bulk Lookup 🏈 | Data from CollegeFootballData.com")
                                await message.channel.send(embed=embed)
                            return

                        except Exception as e:
                            logger.error(f"❌ Error in bulk player lookup: {e}", exc_info=True)
                            await thinking_msg.edit(content=f"❌ Error looking up players: {str(e)}")
                            return

                # First check if it's a CFB data query using our comprehensive parser
                cfb_query = player_lookup.parse_cfb_query(message.content)
                query_type = cfb_query.get('type')

                if query_type:
                    logger.info(f"🏈 CFB query detected - type: {query_type}, data: {cfb_query}")
                    thinking_msg = await message.channel.send(f"🔍 Looking that up, hang on...")

                    try:
                        if query_type == 'rankings':
                            team = cfb_query.get('team')
                            if team:
                                result = await player_lookup.get_team_ranking(team)
                                response = player_lookup.format_team_ranking(result)
                                title = f"📊 {team} Rankings"
                            else:
                                result = await player_lookup.get_rankings()
                                response = player_lookup.format_rankings(result)
                                title = "📊 College Football Rankings"
                            await thinking_msg.delete()
                            embed = discord.Embed(title=title, description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                        elif query_type == 'matchup':
                            team1 = cfb_query.get('team1')
                            team2 = cfb_query.get('team2')
                            result = await player_lookup.get_matchup_history(team1, team2)
                            response = player_lookup.format_matchup(result)
                            await thinking_msg.delete()
                            embed = discord.Embed(title=f"🏈 {team1} vs {team2}", description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                        elif query_type == 'schedule':
                            team = cfb_query.get('team')
                            result = await player_lookup.get_team_schedule(team)
                            response = player_lookup.format_schedule(result, team)
                            await thinking_msg.delete()
                            embed = discord.Embed(title=f"📅 {team} Schedule", description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                        elif query_type == 'draft':
                            team = cfb_query.get('team')
                            result = await player_lookup.get_draft_picks(team)
                            response = player_lookup.format_draft_picks(result, team)
                            await thinking_msg.delete()
                            embed = discord.Embed(title=f"🏈 NFL Draft Picks", description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                        elif query_type == 'transfers':
                            team = cfb_query.get('team')
                            result = await player_lookup.get_team_transfers(team)
                            response = player_lookup.format_transfers(result, team)
                            await thinking_msg.delete()
                            embed = discord.Embed(title=f"🔄 {team} Transfers", description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                        elif query_type == 'betting':
                            team1 = cfb_query.get('team1')
                            team2 = cfb_query.get('team2')
                            result = await player_lookup.get_betting_lines(team=team1)
                            response = player_lookup.format_betting_lines(result)
                            await thinking_msg.delete()
                            embed = discord.Embed(title=f"💰 Betting Lines", description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                        elif query_type == 'ratings':
                            team = cfb_query.get('team')
                            result = await player_lookup.get_team_ratings(team)
                            response = player_lookup.format_ratings(result)
                            await thinking_msg.delete()
                            embed = discord.Embed(title=f"📈 {team} Ratings", description=response, color=0x1e90ff)
                            embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
                            await message.channel.send(embed=embed)
                            return

                    except Exception as e:
                        logger.error(f"❌ Error in CFB query: {e}", exc_info=True)
                        await thinking_msg.edit(content=f"❌ Error looking that up: {str(e)}")
                        return

                # Fall back to player lookup if no other query type matched
                player_keywords = ['from', 'player', 'stats', 'what do you know', 'tell me about', 'who is', 'info on', 'lookup']
                # Check for player-related queries (but not league rule queries)
                if any(kw in message_lower for kw in player_keywords) and not any(term in message_lower for term in ['rule', 'charter', 'policy', 'advance']):
                    # Use the player_lookup parser
                    parsed = player_lookup.parse_player_query(message.content)
                    if parsed.get('name') and len(parsed['name']) > 2:
                        logger.info(f"🏈 Player lookup request from {message.author}: {message.content}")

                        thinking_msg = await message.channel.send("🔍 Looking up that player, hang on...")

                        try:
                            name = parsed.get('name')
                            team = parsed.get('team')

                            logger.info(f"🔍 Searching for player: {name}" + (f" from {team}" if team else ""))

                            player_info = await player_lookup.get_full_player_info(name, team)

                            await thinking_msg.delete()

                            if player_info:
                                response = player_lookup.format_player_response(player_info)
                                embed = discord.Embed(
                                    title="🏈 Player Info",
                                    description=response,
                                    color=0x1e90ff
                                )

                                # Check if it's an Oregon player and add snark (Harry always hates Oregon)
                                player_team = player_info.get('player', {}).get('team', '').lower()
                                if 'oregon' in player_team and 'oregon state' not in player_team:
                                    embed.set_footer(text="Harry's Player Lookup 🏈 | Though why you'd care about a Duck is beyond me...")
                                else:
                                    embed.set_footer(text="Harry's Player Lookup 🏈 | Data from CollegeFootballData.com")

                                await message.channel.send(embed=embed)
                            else:
                                embed = discord.Embed(
                                    title="❓ Player Not Found",
                                    description=f"Couldn't find a player matching **{name}**" + (f" from **{team}**" if team else "") + ".",
                                    color=0xff6600
                                )
                                embed.add_field(
                                    name="💡 Tips",
                                    value="• Check the spelling\n• Use full name (First Last)\n• FCS/smaller schools may have limited data\n• Try without the team name",
                                    inline=False
                                )
                                embed.set_footer(text="Harry's Player Lookup 🏈 | Data from CollegeFootballData.com")
                                await message.channel.send(embed=embed)
                            return

                        except Exception as e:
                            logger.error(f"❌ Error in player lookup: {e}", exc_info=True)
                            await thinking_msg.edit(content=f"❌ Error looking up player: {str(e)}")
                            return

            # Check if this is a rule scan request (e.g., "scan #channel for rules")
            rule_scan_patterns = [
                r'scan\s+(?:<#(\d+)>|#?(\w+[-\w]*))\s+for\s+(?:rule|voting|changes)',
                r'check\s+(?:<#(\d+)>|#?(\w+[-\w]*))\s+for\s+(?:rule|voting|changes)',
                r'find\s+(?:rule|voting)\s+(?:changes\s+)?in\s+(?:<#(\d+)>|#?(\w+[-\w]*))',
                r'what\s+rules?\s+(?:passed|changed|were voted)\s+in\s+(?:<#(\d+)>|#?(\w+[-\w]*))',
            ]

            channel_to_scan = None
            for pattern in rule_scan_patterns:
                match = re.search(pattern, message.content, re.IGNORECASE)
                if match:
                    # Try to get channel from mention or name
                    channel_id = match.group(1) if match.group(1) else None
                    channel_name = match.group(2) if len(match.groups()) > 1 and match.group(2) else None

                    if channel_id:
                        channel_to_scan = message.guild.get_channel(int(channel_id))
                    elif channel_name and message.guild:
                        # Try to find channel by name
                        for ch in message.guild.text_channels:
                            if ch.name.lower() == channel_name.lower() or channel_name.lower() in ch.name.lower():
                                channel_to_scan = ch
                                break
                    break

            if channel_to_scan and bot_mentioned and admin_manager and admin_manager.is_admin(message.author, message):
                if not charter_editor or not channel_summarizer or not AI_AVAILABLE:
                    await message.channel.send("❌ Required components not available for rule scanning")
                    return

                logger.info(f"📜 Rule scan request from {message.author} for #{channel_to_scan.name}")

                thinking_msg = await message.channel.send(f"🔍 Scanning #{channel_to_scan.name} for rule changes...")

                try:
                    # Fetch and analyze messages
                    messages_list = await channel_summarizer.fetch_messages(channel_to_scan, hours=168, limit=500)

                    if not messages_list:
                        await thinking_msg.edit(content=f"❌ No messages found in #{channel_to_scan.name}")
                        return

                    formatted = [f"[{m.author.display_name}]: {m.content}" for m in messages_list]
                    rule_changes = await charter_editor.find_rule_changes_in_messages(formatted, channel_to_scan.name)

                    await thinking_msg.delete()

                    if not rule_changes:
                        embed = discord.Embed(
                            title=f"📜 Rule Scan: #{channel_to_scan.name}",
                            description="No rule changes or votes found in the last week.",
                            color=0xffaa00
                        )
                        await message.channel.send(embed=embed)
                        return

                    # Show found rules
                    embed = discord.Embed(
                        title=f"📜 Rule Changes Found in #{channel_to_scan.name}",
                        description=f"Found **{len(rule_changes)}** rule changes/votes",
                        color=0x1e90ff
                    )

                    passed_rules = []
                    for i, rule in enumerate(rule_changes[:8], 1):
                        status = rule.get("status", "unknown")
                        emoji = {"passed": "✅", "failed": "❌", "proposed": "📋", "decided": "✅"}.get(status, "❓")

                        votes = ""
                        if rule.get("votes_for") is not None:
                            votes = f" ({rule.get('votes_for', 0)}-{rule.get('votes_against', 0)})"

                        rule_text = rule.get("rule", "Unknown rule")
                        context = rule.get("context", "")

                        field_value = f"📝 {rule_text}"
                        if context and context.strip() and context.lower() != rule_text.lower():
                            field_value += f"\n> _{context}_"

                        if len(field_value) > 500:
                            field_value = field_value[:497] + "..."

                        embed.add_field(name=f"{emoji} {status.upper()}{votes}", value=field_value, inline=False)

                        if status in ["passed", "decided"]:
                            passed_rules.append(rule)

                    if passed_rules:
                        embed.add_field(
                            name="🔧 Update Charter?",
                            value=f"Found **{len(passed_rules)}** passed rules. React with 📝 to generate charter updates.",
                            inline=False
                        )

                    msg = await message.channel.send(embed=embed)

                    if passed_rules:
                        await msg.add_reaction("📝")
                        if not hasattr(bot, 'pending_rule_scans'):
                            bot.pending_rule_scans = {}
                        bot.pending_rule_scans[msg.id] = {
                            "user_id": message.author.id,
                            "user_name": message.author.display_name,
                            "rule_changes": passed_rules,
                            "channel_name": channel_to_scan.name,
                            "expires": datetime.now().timestamp() + 600  # 10 minute timeout
                        }

                except Exception as e:
                    logger.error(f"❌ Error in rule scan: {e}", exc_info=True)
                    await thinking_msg.edit(content=f"❌ Error scanning: {str(e)}")

                return

            elif channel_to_scan and bot_mentioned:
                embed = discord.Embed(
                    title="❌ Permission Denied",
                    description="You need to be a bot admin to scan for rules, ya muppet!",
                    color=0xff0000
                )
                await message.channel.send(embed=embed)
                return

        # Step 1: Check if this is a channel summary request
        question_lower = message.content.lower()

        # Keywords that indicate a summary request
        summary_keywords = [
            'summarize', 'summary', 'what happened', 'tell me what happened',
            'recap', 'what\'s been going on', 'what passed', 'what was approved',
            'what was voted', 'what rules passed', 'what rules were approved',
            'what did we vote', 'what did we approve', 'what changed'
        ]

        # Check for time references (e.g., "last 3 hours", "past 24 hours", "in the last day")
        time_patterns = [
            r'(\d+)\s*(?:hour|hr|h)',
            r'last\s+(\d+)\s*(?:hour|hr|h)',
            r'past\s+(\d+)\s*(?:hour|hr|h)',
            r'in\s+the\s+last\s+(\d+)\s*(?:hour|hr|h)',
            r'over\s+the\s+last\s+(\d+)\s*(?:hour|hr|h)'
        ]

        summary_hours = None
        has_time_reference = False
        for pattern in time_patterns:
            hours_match = re.search(pattern, question_lower)
            if hours_match:
                summary_hours = int(hours_match.group(1))
                has_time_reference = True
                break

        # Check if it's asking about channel activity/history
        is_asking_about_channel = any(keyword in question_lower for keyword in summary_keywords)

        # It's a summary request if:
        # 1. Has explicit summary keywords (summarize, recap, etc.)
        # 2. Has time reference AND asks about what happened/passed/approved (channel activity)
        is_summary_request = is_asking_about_channel or (has_time_reference and any(
            phrase in question_lower for phrase in ['what happened', 'what passed', 'what was', 'what did', 'what changed', 'what rules']
        ))

        # Log summary detection for debugging
        if bot_mentioned:
            logger.info(f"🔍 Summary detection: has_time={has_time_reference}, asking_about_channel={is_asking_about_channel}, is_summary={is_summary_request}, hours={summary_hours}")

        # If it's a summary request and bot is mentioned, use the summarizer
        if is_summary_request and bot_mentioned and channel_summarizer:
            try:
                hours = summary_hours or 24  # Default to 24 hours if not specified
                logger.info(f"📊 Summary requested via @mention by {message.author} - {hours} hours")

                # Use summarizer to generate summary
                summary = await channel_summarizer.get_channel_summary(
                    message.channel,
                    hours=hours,
                    focus=None,  # Could extract focus from message if needed
                    limit=500
                )

                if summary:
                    embed = discord.Embed(
                        title=f"📊 Channel Summary - Last {hours} {'Hour' if hours == 1 else 'Hours'}",
                        description=summary,
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="📍 Channel",
                        value=f"#{message.channel.name}",
                        inline=True
                    )
                    embed.add_field(
                        name="⏰ Time Period",
                        value=f"Last {hours} {'hour' if hours == 1 else 'hours'}",
                        inline=True
                    )
                    embed.set_footer(text=f"Harry's Channel Summary 🏈 | Requested by {message.author.display_name}")
                    await message.channel.send(embed=embed)
                    logger.info(f"✅ Summary delivered via @mention for #{message.channel.name}")
                    return  # Don't continue with AI response
                else:
                    # Fall through to AI response if summarizer fails
                    pass
            except Exception as e:
                logger.error(f"❌ Error generating summary via @mention: {e}")
                # Fall through to AI response

        # Step 2: Try AI with charter content first
        ai_response = None
        if AI_AVAILABLE and ai_assistant:
            try:
                question = message.content
                if bot_mentioned:
                    # Remove the mention from the question
                    question = question.replace(f'<@{bot.user.id}>', '').strip()

                # Use league-specific AI logic for mentions or allowed channels
                # Bot was mentioned or channel allows unprompted responses
                if bot_mentioned or channel_allows_unprompted:
                    # Determine if this is a league-related question
                    is_league_related = any(f' {keyword} ' in f' {question.lower()} ' for keyword in LEAGUE_KEYWORDS)

                    # Get personality prompt based on server settings
                    personality = server_config.get_personality_prompt(guild_id)

                    if is_league_related:
                        # Step 1: Try AI with charter content for league questions
                        charter_question = f"""{personality} Answer this question using ONLY the league charter content:

Question: {question}

If the charter contains relevant information, provide a helpful answer. If not, respond with "NO_CHARTER_INFO"."""

                        # Log the question and who asked it
                        logger.info(f"🤖 League AI Question from {message.author} ({message.author.id}): {question}")
                        logger.info(f"📝 Full AI prompt: {charter_question[:200]}...")

                        ai_response = await ai_assistant.ask_ai(charter_question, f"{message.author} ({message.author.id})")

                        # Step 2: If no charter info, try general AI search without charter context
                        if ai_response and "NO_CHARTER_INFO" in ai_response:
                            logger.info("No charter info found, trying general AI search without charter context")
                            general_question = f"""{personality} Answer this question about CFB 26 league rules, recruiting, transfers, or dynasty management:

Question: {question}

IMPORTANT: Only provide a direct answer if you're confident about CFB 26 league specifics. If you're not sure about the exact league rules, say "I don't have that specific information about our league rules, but you can check our full charter for the official details."

Keep responses concise and helpful. Do NOT mention "charter" unless you truly don't know the answer."""

                            # Log the general AI question
                            logger.info(f"🤖 General AI Question from {message.author} ({message.author.id}): {question}")
                            logger.info(f"📝 General AI prompt: {general_question[:200]}...")
                            logger.info("🌍 Fallback to general AI without charter context")

                            # Use AI without charter context since charter had no info
                            general_context = personality

                            # Call OpenAI directly with general context
                            ai_response = await ai_assistant.ask_openai(general_question, general_context, personality_prompt=personality)
                            if not ai_response:
                                # Fallback to Anthropic
                                ai_response = await ai_assistant.ask_anthropic(general_question, general_context, personality_prompt=personality)
                    else:
                        # For non-league questions, use general AI WITHOUT charter context
                        general_question = f"""{personality} Answer this question helpfully and accurately:

Question: {question}

Please provide a helpful, accurate answer."""

                        # Log the general AI question
                        logger.info(f"🤖 General AI Question from {message.author} ({message.author.id}): {question}")
                        logger.info(f"📝 General AI prompt: {general_question[:200]}...")
                        logger.info("🌍 General question - using AI without charter context")

                        # Use AI without charter context (like /ask command)
                        general_context = personality

                        # Call OpenAI directly with general context
                        ai_response = await ai_assistant.ask_openai(general_question, general_context, personality_prompt=personality)
                        if not ai_response:
                            # Fallback to Anthropic
                            ai_response = await ai_assistant.ask_anthropic(general_question, general_context, personality_prompt=personality)
                else:
                    # For non-allowed channels, this should only happen with slash commands
                    # Use general AI without league context
                    personality = server_config.get_personality_prompt(guild_id)
                    general_question = f"""{personality} Answer this question helpfully and accurately:

Question: {question}

Please provide a helpful, accurate answer. This is a general conversation, not about league rules."""

                    logger.info(f"🤖 General AI Question from {message.author} ({message.author.id}): {question}")
                    logger.info(f"📝 General AI prompt: {general_question[:200]}...")
                    logger.info("🌍 General question - using AI without charter context")

                    # Use AI without charter context
                    general_context = personality

                    # Call OpenAI directly with general context
                    ai_response = await ai_assistant.ask_openai(general_question, general_context, personality_prompt=personality)
                    if not ai_response:
                        # Fallback to Anthropic
                        ai_response = await ai_assistant.ask_anthropic(general_question, general_context)

            except Exception as e:
                logger.error(f"AI error: {e}")
                ai_response = None

        # Use AI response if available, otherwise fall back to generic
        if ai_response and "NO_CHARTER_INFO" not in ai_response:
            embed.description = ai_response
            # Only add charter link if AI indicates it doesn't know the answer
            if "check the full charter" in ai_response.lower() or "charter" in ai_response.lower():
                embed.add_field(
                    name="📖 Full League Charter",
                    value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
                    inline=False
                )
        else:
            embed.description = "Well, you stumped me! But check our charter below - it has all the official CFB 26 league rules, recruiting policies, and dynasty management guidelines!"
            # Always add charter link for generic responses
            embed.add_field(
                name="📖 Full League Charter",
                value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
                inline=False
            )

        embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")

        # Send the response
        await message.channel.send(embed=embed)

    # PRIORITY 3: Handle direct mentions that aren't league-related
    elif bot_mentioned:
        logger.info(f"💬 Direct mention but not league-related: '{message.content}' (Server: {guild_name})")

        # Don't respond to slash commands
        if message.content.startswith('/'):
            return

        # Add a small delay to make it feel more natural
        await asyncio.sleep(1)

        # Create a friendly response redirecting to league topics
        embed = discord.Embed(
            title="🏈 Harry's Response",
            color=0x1e90ff
        )
        embed.description = "Hey there! I'm Harry, your CFB 26 league assistant! I'm here to help with league rules, recruiting, transfers, dynasty management, and all things college football. Ask me about our league charter, game settings, or anything CFB 26 related!"
        embed.add_field(
            name="📖 Full League Charter",
            value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
            inline=False
        )
        embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")

        # Send the response
        await message.channel.send(embed=embed)

    else:
        logger.info(f"❌ No response triggers met")

    # Process other bot commands
    await bot.process_commands(message)

async def safe_clear_reactions(message):
    """Safely clear reactions - doesn't fail if bot lacks Manage Messages permission"""
    try:
        await message.clear_reactions()
    except discord.errors.Forbidden:
        logger.debug("Could not clear reactions - missing Manage Messages permission")
    except Exception as e:
        logger.debug(f"Could not clear reactions: {e}")


@bot.event
async def on_reaction_add(reaction, user):
    """Handle emoji reactions"""
    logger.debug(f"🔔 Reaction event: {reaction.emoji} by {user.display_name} on msg {reaction.message.id}")

    # Ignore reactions from the bot itself
    if user == bot.user:
        logger.debug("  Ignoring bot's own reaction")
        return

    # Only respond to reactions on Harry's messages
    if reaction.message.author != bot.user:
        logger.debug("  Ignoring reaction on non-Harry message")
        return

    logger.info(f"📝 Processing reaction: {reaction.emoji} from {user.display_name}")

    # Handle charter update confirmations
    if hasattr(bot, 'pending_charter_updates') and reaction.message.id in bot.pending_charter_updates:
        pending = bot.pending_charter_updates[reaction.message.id]

        # Only the original requester can confirm/cancel
        if user.id != pending["user_id"]:
            return

        # Check if expired
        if datetime.now().timestamp() > pending["expires"]:
            del bot.pending_charter_updates[reaction.message.id]
            await reaction.message.edit(embed=discord.Embed(
                title="⏰ Update Expired",
                description="This charter update request has expired. Please try again.",
                color=0xff6600
            ))
            return

        if str(reaction.emoji) == "✅":
            # Apply the update
            if charter_editor and pending.get("new_charter"):
                success = await charter_editor.apply_update(
                    new_charter=pending["new_charter"],
                    user_id=pending["user_id"],
                    user_name=pending["user_name"],
                    description=pending["description"],
                    before_text=pending.get("before"),
                    after_text=pending.get("after")
                )

                if success:
                    embed = discord.Embed(
                        title="✅ Charter Updated!",
                        description=f"**{pending['description']}**\n\nThe charter has been updated and backed up automatically.",
                        color=0x00ff00
                    )
                    embed.set_footer(text=f"Updated by {pending['user_name']} 🏈")
                    await reaction.message.edit(embed=embed)
                    await safe_clear_reactions(reaction.message)
                    logger.info(f"✅ Charter updated by {pending['user_name']}: {pending['description']}")
                else:
                    embed = discord.Embed(
                        title="❌ Update Failed",
                        description="Failed to apply the charter update. Check the logs for details.",
                        color=0xff0000
                    )
                    await reaction.message.edit(embed=embed)
                    await safe_clear_reactions(reaction.message)

            del bot.pending_charter_updates[reaction.message.id]
            return

        elif str(reaction.emoji) == "❌":
            # Cancel the update
            embed = discord.Embed(
                title="❌ Update Cancelled",
                description="Charter update has been cancelled. No changes were made.",
                color=0xff6600
            )
            await reaction.message.edit(embed=embed)
            await safe_clear_reactions(reaction.message)
            del bot.pending_charter_updates[reaction.message.id]
            logger.info(f"❌ Charter update cancelled by {pending['user_name']}")
            return

    # Handle rule scan -> charter update requests
    # Log what's in pending_rule_scans for debugging
    if hasattr(bot, 'pending_rule_scans'):
        logger.debug(f"  pending_rule_scans keys: {list(bot.pending_rule_scans.keys())}")
        logger.debug(f"  Looking for msg_id: {reaction.message.id}")

    if hasattr(bot, 'pending_rule_scans') and reaction.message.id in bot.pending_rule_scans:
        pending = bot.pending_rule_scans[reaction.message.id]
        logger.info(f"📝 Rule scan reaction: {reaction.emoji} from {user.display_name} on msg {reaction.message.id}")

        # Only the original requester can trigger
        if user.id != pending["user_id"]:
            logger.info(f"⚠️ Wrong user reacted: {user.id} != {pending['user_id']}")
            return

        # Check if expired
        if datetime.now().timestamp() > pending["expires"]:
            logger.info(f"⚠️ Rule scan expired for msg {reaction.message.id}")
            del bot.pending_rule_scans[reaction.message.id]
            return

        logger.info(f"✅ Processing rule scan reaction: {reaction.emoji}")

        if str(reaction.emoji) == "📝":
            # Generate charter updates from the found rules
            await safe_clear_reactions(reaction.message)

            thinking_embed = discord.Embed(
                title="🔧 Generating Charter Updates...",
                description="Analyzing passed rules and generating charter updates...",
                color=0xffaa00
            )
            await reaction.message.edit(embed=thinking_embed)

            try:
                # Generate updates
                updates = await charter_editor.generate_charter_updates_from_rules(
                    pending["rule_changes"]
                )

                if not updates:
                    embed = discord.Embed(
                        title="📜 No Updates Needed",
                        description="The passed rules are either already in the charter or couldn't be automatically applied.",
                        color=0x00ff00
                    )
                    await reaction.message.edit(embed=embed)
                    del bot.pending_rule_scans[reaction.message.id]
                    return

                # Show the suggested updates
                embed = discord.Embed(
                    title="📝 Suggested Charter Updates",
                    description=f"Based on passed rules in #{pending['channel_name']}",
                    color=0x1e90ff
                )

                for i, update in enumerate(updates[:5], 1):  # Show max 5
                    action = update.get("action", "update")
                    action_emoji = "➕" if action == "add" else "✏️"

                    new_text = update.get("new_text", "")[:200]
                    if len(update.get("new_text", "")) > 200:
                        new_text += "..."

                    embed.add_field(
                        name=f"{action_emoji} {update.get('rule_description', 'Update')[:50]}",
                        value=f"**Section:** {update.get('section', 'Unknown')}\n```\n{new_text}\n```",
                        inline=False
                    )

                embed.add_field(
                    name="⚠️ Apply Updates?",
                    value="React with ✅ to apply ALL these updates, or ❌ to cancel.\n*Each change will be backed up automatically.*",
                    inline=False
                )

                await reaction.message.edit(embed=embed)
                await reaction.message.add_reaction("✅")
                await reaction.message.add_reaction("❌")

                # Update the pending data with the generated updates
                pending["generated_updates"] = updates
                pending["expires"] = datetime.now().timestamp() + 120  # Reset timeout

            except Exception as e:
                logger.error(f"❌ Error generating charter updates: {e}", exc_info=True)
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to generate updates: {str(e)}",
                    color=0xff0000
                )
                await reaction.message.edit(embed=embed)
                del bot.pending_rule_scans[reaction.message.id]

            return

        elif str(reaction.emoji) == "✅" and pending.get("generated_updates"):
            # Apply the generated updates
            await safe_clear_reactions(reaction.message)

            updates = pending["generated_updates"]
            current_charter = charter_editor.read_charter()

            if not current_charter:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Could not read current charter",
                    color=0xff0000
                )
                await reaction.message.edit(embed=embed)
                del bot.pending_rule_scans[reaction.message.id]
                return

            # Apply updates one by one
            applied = 0
            new_charter = current_charter

            for update in updates:
                old_text = update.get("old_text")
                new_text = update.get("new_text")

                if update.get("action") == "add":
                    # Add new content at end of relevant section or end of charter
                    section = update.get("section", "")
                    # Simple append for now
                    new_charter = new_charter + f"\n\n{new_text}"
                    applied += 1
                elif old_text and new_text and old_text in new_charter:
                    new_charter = new_charter.replace(old_text, new_text, 1)
                    applied += 1

            if applied > 0:
                success = await charter_editor.apply_update(
                    new_charter=new_charter,
                    user_id=pending["user_id"],
                    user_name=pending["user_name"],
                    description=f"Applied {applied} rule updates from #{pending['channel_name']}",
                    before_text=f"Applied {applied} updates from voting",
                    after_text=f"Rules from #{pending['channel_name']}"
                )

                if success:
                    embed = discord.Embed(
                        title="✅ Charter Updated!",
                        description=f"Applied **{applied}** rule updates from #{pending['channel_name']}!\n\nBackup created automatically.",
                        color=0x00ff00
                    )
                    embed.set_footer(text=f"Updated by {pending['user_name']} 🏈")
                else:
                    embed = discord.Embed(
                        title="❌ Update Failed",
                        description="Failed to apply updates to the charter.",
                        color=0xff0000
                    )
            else:
                embed = discord.Embed(
                    title="⚠️ No Updates Applied",
                    description="Could not apply any updates - text may not match exactly.",
                    color=0xffaa00
                )

            await reaction.message.edit(embed=embed)
            del bot.pending_rule_scans[reaction.message.id]
            return

        elif str(reaction.emoji) == "❌":
            embed = discord.Embed(
                title="❌ Updates Cancelled",
                description="Charter updates cancelled. No changes were made.",
                color=0xff6600
            )
            await reaction.message.edit(embed=embed)
            await safe_clear_reactions(reaction.message)
            del bot.pending_rule_scans[reaction.message.id]
            return

    # Handle different emoji reactions
    if reaction.emoji == '❓':
        # Question mark - offer help
        embed = discord.Embed(
            title="🏈 Harry's Help",
            description="I'm here to help with CFB 26 league questions! Here are some ways to interact with me:",
            color=0x1e90ff
        )

        embed.add_field(
            name="💬 Chat Commands:",
            value="• Mention me: `@Harry what are the rules?`\n• Ask questions: `What's the transfer policy?`\n• Say hi: `Hi Harry!`",
            inline=False
        )

        embed.add_field(
            name="⚡ Slash Commands:",
            value="• `/harry <question>` - Ask me anything\n• `/charter` - Link to full charter\n• `/help_cfb` - See all commands",
            inline=False
        )

        embed.add_field(
            name="📖 Full Charter",
            value="[Open Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
            inline=False
        )

        embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")

        await reaction.message.channel.send(embed=embed)

    elif reaction.emoji == '🏈':
        # Football emoji - CFB enthusiasm
        embed = discord.Embed(
            title="🏈 CFB 26 Hype!",
            description="CFB 26 is the best dynasty league! 🏆\n\nNeed help with league rules? Just ask me anything!",
            color=0x1e90ff
        )
        await reaction.message.channel.send(embed=embed)

    elif reaction.emoji == '🦆':
        # Duck emoji - Oregon rivalry (only if auto_responses is on)
        reaction_guild_id = reaction.message.guild.id if reaction.message.guild else 0
        if server_config.auto_responses_enabled(reaction_guild_id):
            embed = discord.Embed(
                title="🦆 Oregon Sucks!",
                description="Oregon sucks! 🦆💩\n\nBut CFB 26 rules are awesome! Ask me about them!",
                color=0x1e90ff
            )
            await reaction.message.channel.send(embed=embed)

    elif reaction.emoji == '🐕':
        # Dog emoji - Huskies support
        embed = discord.Embed(
            title="🐕 Go Huskies!",
            description="Go Huskies! 🐕\n\nSpeaking of teams, need help with league rules?",
            color=0x1e90ff
        )
        await reaction.message.channel.send(embed=embed)

    elif reaction.emoji == '🤖':
        # Robot emoji - AI explanation
        embed = discord.Embed(
            title="🤖 AI Assistant",
            description="I'm powered by AI to help with your CFB 26 league questions! Ask me anything about rules, recruiting, transfers, or penalties!",
            color=0x1e90ff
        )
        await reaction.message.channel.send(embed=embed)

    elif reaction.emoji == '💡':
        # Lightbulb emoji - tips
        embed = discord.Embed(
            title="💡 Pro Tips",
            description="Here are some pro tips for CFB 26:\n\n• Follow all league rules to avoid penalties\n• Recruit smart - quality over quantity\n• Use the right difficulty settings\n• Don't sim games without permission\n\nNeed more help? Just ask!",
            color=0x1e90ff
        )
        await reaction.message.channel.send(embed=embed)

async def load_league_data():
    """Load league rules and data from JSON files"""
    try:
        with open('data/league_rules.json', 'r') as f:
            bot.league_data = json.load(f)
        logger.info("✅ League data loaded successfully")
    except FileNotFoundError:
        logger.warning("⚠️  League data file not found - using default data")
        bot.league_data = {"league_info": {"name": "CFB 26 Online Dynasty"}}
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing league data: {e}")
        bot.league_data = {"league_info": {"name": "CFB 26 Online Dynasty"}}

@bot.tree.command(name="rule", description="Look up CFB 26 league rules")
async def rule(interaction: discord.Interaction, rule_name: str):
    """Look up a specific league rule"""
    await interaction.response.send_message("📋 Looking up rule...", ephemeral=True)

    # Search for rule in league data
    rule_found = False
    embed = discord.Embed(
        title=f"CFB 26 League Rule: {rule_name.title()}",
        color=0x1e90ff
    )

    # Search through league rules (if any exist)
    if hasattr(bot, 'league_data') and 'rules' in bot.league_data:
        for category, rules in bot.league_data['rules'].items():
            if rule_name.lower() in category.lower():
                embed.description = rules.get('description', 'Rule information available')
                if 'topics' in rules:
                    topics_text = '\n'.join([f"• {topic}" for topic in rules['topics'].keys()])
                    embed.add_field(name="Related Topics", value=topics_text, inline=False)
                rule_found = True
                break

    # If no specific rule found, provide general guidance
    if not rule_found:
        embed.description = f"Specific rule '{rule_name}' not found in local data. All CFB 26 league rules are in the official charter."

    # Always add the charter link
    embed.add_field(
        name="📖 Full League Charter",
        value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="recruiting", description="Get recruiting rules and policies")
async def recruiting(interaction: discord.Interaction, topic: str):
    """Get information about recruiting rules"""
    await interaction.response.defer()

    embed = discord.Embed(
        title=f"CFB 26 Recruiting: {topic.title()}",
        color=0x32cd32
    )

    # Check if recruiting rules exist
    if hasattr(bot, 'league_data') and 'rules' in bot.league_data and 'recruiting' in bot.league_data['rules']:
        recruiting_rules = bot.league_data['rules']['recruiting']
        embed.description = recruiting_rules.get('description', 'Recruiting rules and policies')

        if 'topics' in recruiting_rules:
            topics = recruiting_rules['topics']
            if topic.lower() in topics:
                embed.add_field(name="Information", value=topics[topic.lower()], inline=False)
            else:
                available_topics = '\n'.join([f"• {t}" for t in topics.keys()])
                embed.add_field(name="Available Topics", value=available_topics, inline=False)
    else:
        embed.description = "Recruiting rules not found in league data."

    embed.add_field(
        name="League Charter",
        value="[View Full Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="team", description="Get team information")
async def team(interaction: discord.Interaction, team_name: str):
    """Get information about a college football team"""
    await interaction.response.defer()

    # TODO: Implement team lookup logic
    embed = discord.Embed(
        title=f"Team: {team_name.title()}",
        description="Team lookup functionality coming soon!",
        color=0x32cd32
    )
    embed.add_field(name="Status", value="🚧 Under Development", inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="dynasty", description="Get dynasty management rules")
async def dynasty(interaction: discord.Interaction, topic: str):
    """Get information about dynasty management rules"""
    await interaction.response.defer()

    embed = discord.Embed(
        title=f"CFB 26 Dynasty: {topic.title()}",
        color=0xff6b6b
    )

    # Check if dynasty rules exist
    if hasattr(bot, 'league_data') and 'rules' in bot.league_data:
        # Look for dynasty-related rules
        dynasty_topics = ['transfers', 'gameplay', 'scheduling', 'conduct']
        found_topic = None

        for dt in dynasty_topics:
            if topic.lower() in dt.lower() and dt in bot.league_data['rules']:
                found_topic = dt
                break

        if found_topic:
            rules = bot.league_data['rules'][found_topic]
            embed.description = rules.get('description', 'Dynasty management rules')

            if 'topics' in rules:
                topics = rules['topics']
                if topic.lower() in topics:
                    embed.add_field(name="Information", value=topics[topic.lower()], inline=False)
                else:
                    available_topics = '\n'.join([f"• {t}" for t in topics.keys()])
                    embed.add_field(name="Available Topics", value=available_topics, inline=False)
        else:
            embed.description = "Dynasty topic not found. Available topics: transfers, gameplay, scheduling, conduct"
    else:
        embed.description = "Dynasty rules not found in league data."

    embed.add_field(
        name="League Charter",
        value="[View Full Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="charter", description="Get link to the official league charter")
async def charter(interaction: discord.Interaction):
    """Get the official league charter link"""
    # Check if league module is enabled
    if not await check_module_enabled(interaction, FeatureModule.LEAGUE):
        return

    embed = discord.Embed(
        title="📋 CFB 26 League Charter",
        description="Official league rules, policies, and guidelines",
        color=0x1e90ff
    )

    embed.add_field(
        name="📖 View Full Charter",
        value="[Open League Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    embed.add_field(
        name="📝 Quick Commands",
        value="Use `/rule <topic>`, `/recruiting <topic>`, or `/dynasty <topic>` for specific information",
        inline=False
    )

    embed.set_footer(text="CFB 26 League Bot - Always check the charter for complete rules")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scan_rules", description="Scan a channel for rule changes and votes")
@discord.app_commands.describe(
    channel="Channel to scan (e.g., #offseason-voting)",
    hours="Hours of history to scan (default: 168 = 1 week)"
)
async def scan_rules(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    hours: int = 168
):
    """Scan a channel for rule changes and offer to update the charter"""
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message(
            "❌ Only admins can scan for rule changes, ya muppet!",
            ephemeral=True
        )
        return

    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    if not channel_summarizer:
        await interaction.response.send_message("❌ Channel summarizer not available", ephemeral=True)
        return

    if not AI_AVAILABLE or not ai_assistant:
        await interaction.response.send_message("❌ AI not available for this analysis", ephemeral=True)
        return

    # Validate hours
    if hours < 24:
        await interaction.response.send_message("❌ Need at least 24 hours of history!", ephemeral=True)
        return
    if hours > 720:  # 30 days max
        await interaction.response.send_message("❌ Max 720 hours (30 days)", ephemeral=True)
        return

    await interaction.response.defer()

    try:
        # Fetch messages from the channel
        messages = await channel_summarizer.fetch_messages(channel, hours=hours, limit=500)

        if not messages:
            await interaction.followup.send(f"❌ No messages found in {channel.mention} in the last {hours} hours")
            return

        # Format messages for analysis - include both text and polls
        formatted_messages = []
        poll_count = 0
        for msg in messages:
            # Add regular message content
            if msg.content:
                formatted_messages.append(f"[{msg.author.display_name}]: {msg.content}")

            # Check for polls (requires discord.py 2.4+)
            try:
                if hasattr(msg, 'poll') and msg.poll:
                    poll_count += 1
                    poll = msg.poll
                    poll_text = f"[{msg.author.display_name}] POLL: {poll.question}"

                    # Add poll answers/options
                    if hasattr(poll, 'answers') and poll.answers:
                        options = []
                        for answer in poll.answers:
                            vote_count = getattr(answer, 'vote_count', 0)
                            answer_text = getattr(answer, 'text', str(answer))
                            options.append(f"  - {answer_text} ({vote_count} votes)")
                        poll_text += "\n" + "\n".join(options)

                    # Add poll status
                    if getattr(poll, 'is_finalized', False):
                        total = getattr(poll, 'total_votes', 0)
                        poll_text += f"\n  STATUS: CLOSED (Total: {total} votes)"
                        victor = getattr(poll, 'victor_answer', None)
                        if victor:
                            victor_text = getattr(victor, 'text', str(victor))
                            poll_text += f" - WINNER: {victor_text}"
                    else:
                        total = getattr(poll, 'total_votes', 0)
                        poll_text += f"\n  STATUS: OPEN (Total: {total} votes so far)"

                    formatted_messages.append(poll_text)
            except Exception as e:
                logger.debug(f"Could not process poll: {e}")

        logger.info(f"📊 Rule scan: Found {len(messages)} messages, {poll_count} polls in #{channel.name}")
        # Log sample of formatted messages for debugging
        if formatted_messages:
            logger.debug(f"📝 First 3 formatted messages for AI:")
            for fm in formatted_messages[:3]:
                logger.debug(f"  - {fm[:100]}...")

        # Find rule changes
        rule_changes = await charter_editor.find_rule_changes_in_messages(
            formatted_messages,
            channel_name=channel.name
        )

        if not rule_changes:
            embed = discord.Embed(
                title=f"📜 Rule Scan: #{channel.name}",
                description=f"No rule changes or votes found in the last {hours} hours.",
                color=0xffaa00
            )
            embed.set_footer(text=f"Scanned {len(messages)} messages ({poll_count} polls)")
            await interaction.followup.send(embed=embed)
            return

        # Create embed showing found rules
        embed = discord.Embed(
            title=f"📜 Rule Changes Found in #{channel.name}",
            description=f"Found **{len(rule_changes)}** rule changes/votes",
            color=0x1e90ff
        )

        passed_rules = []
        for i, rule in enumerate(rule_changes[:10], 1):  # Show max 10
            status = rule.get("status", "unknown")
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "proposed": "📋",
                "decided": "✅"
            }.get(status, "❓")

            votes = ""
            if rule.get("votes_for") is not None:
                votes = f" ({rule.get('votes_for', 0)}-{rule.get('votes_against', 0)})"

            # Build detailed rule text
            rule_text = rule.get("rule", "Unknown rule")
            context = rule.get("context", "")

            # Format the field value with rule and context
            field_value = f"📝 {rule_text}"
            if context and context.strip() and context.lower() != rule_text.lower():
                field_value += f"\n> _{context}_"

            # Truncate if too long (Discord field limit is 1024)
            if len(field_value) > 500:
                field_value = field_value[:497] + "..."

            logger.debug(f"Rule scan field: rule='{rule_text[:30]}...', context='{context[:30] if context else 'NONE'}...'")

            embed.add_field(
                name=f"{i}. {status_emoji} {status.upper()}{votes}",
                value=field_value,
                inline=False
            )

            if status in ["passed", "decided"]:
                passed_rules.append(rule)

        embed.set_footer(text=f"Scanned {len(messages)} messages ({poll_count} polls) over {hours} hours")

        if passed_rules:
            embed.add_field(
                name="🔧 Update Charter?",
                value=f"Found **{len(passed_rules)}** passed rules. React with 📝 to generate charter updates.",
                inline=False
            )

        msg = await interaction.followup.send(embed=embed)

        if passed_rules:
            await msg.add_reaction("📝")

            # Store for reaction handler
            if not hasattr(bot, 'pending_rule_scans'):
                bot.pending_rule_scans = {}

            bot.pending_rule_scans[msg.id] = {
                "user_id": interaction.user.id,
                "user_name": interaction.user.display_name,
                "rule_changes": passed_rules,
                "channel_name": channel.name,
                "expires": datetime.now().timestamp() + 600  # 10 minute timeout
            }
            logger.info(f"📝 Stored pending rule scan: msg_id={msg.id}, user={interaction.user.id}, rules={len(passed_rules)}")

        logger.info(f"📜 Rule scan completed for #{channel.name} by {interaction.user}")

    except Exception as e:
        logger.error(f"❌ Error scanning rules: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error scanning for rules: {str(e)}")

@bot.tree.command(name="sync_charter", description="Sync charter to Discord for persistence (Admin only)")
async def sync_charter(interaction: discord.Interaction):
    """Manually sync the charter file to Discord for persistence across deployments"""
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ Only admins can sync the charter!", ephemeral=True)
        return

    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # Read current file and save to Discord
    content = charter_editor.read_charter()
    if not content:
        await interaction.followup.send("❌ No charter file found to sync!", ephemeral=True)
        return

    success = await charter_editor.save_to_discord(content)

    if success:
        await interaction.followup.send(
            f"✅ Charter synced to Discord!\n\n"
            f"📄 **{len(content)}** characters saved\n"
            f"💾 Will persist across bot restarts/deployments",
            ephemeral=True
        )
        logger.info(f"📜 Charter manually synced to Discord by {interaction.user}")
    else:
        await interaction.followup.send("❌ Failed to sync charter to Discord", ephemeral=True)


@bot.tree.command(name="charter_history", description="View recent charter changes")
async def charter_history(interaction: discord.Interaction):
    """View recent charter update history"""
    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    changes = charter_editor.get_recent_changes(limit=10)

    if not changes:
        embed = discord.Embed(
            title="📜 Charter History",
            description="No charter changes have been recorded yet.",
            color=0x1e90ff
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="📜 Charter Update History",
        description="Recent changes to the league charter",
        color=0x1e90ff
    )

    for i, change in enumerate(changes[:5], 1):  # Show top 5
        timestamp = change.get("timestamp", "Unknown")
        if isinstance(timestamp, str) and "T" in timestamp:
            # Format ISO timestamp nicely
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%b %d, %Y %I:%M %p")
            except (ValueError, TypeError):
                pass  # Keep original timestamp if parsing fails

        user_name = change.get("user_name", "Unknown")
        description = change.get("description", "No description")

        embed.add_field(
            name=f"{i}. {timestamp}",
            value=f"**By:** {user_name}\n**Change:** {description[:100]}{'...' if len(description) > 100 else ''}",
            inline=False
        )

    embed.set_footer(text="Use @Harry to update charter rules interactively 🏈")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help_cfb", description="Show all available commands")
async def help_cfb(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="🏈 CFB 26 League Bot Commands",
        description="Oi! Here's what I can do for ya, mate! **v1.3.0**",
        color=0x1e90ff
    )

    # AI Commands
    embed.add_field(
        name="🤖 **AI Assistant**",
        value=(
            "• `/harry <question>` - Ask me league questions\n"
            "• `/ask <question>` - General AI answers\n"
            "• `@Harry <message>` - Chat naturally!"
        ),
        inline=False
    )

    # Dynasty Week Commands
    embed.add_field(
        name="📅 **Dynasty Week**",
        value=(
            "• `/week` - Current week, phase & actions\n"
            "• `/weeks` - Full 30-week schedule\n"
            "• `/set_season_week` - Set week **(Admin)**"
        ),
        inline=True
    )

    # Advance Timer Commands
    embed.add_field(
        name="⏰ **Advance Timer**",
        value=(
            "• `/advance [hours]` - Start countdown **(Admin)**\n"
            "• `/time_status` - Check progress\n"
            "• `/stop_countdown` - Stop timer **(Admin)**\n"
            "• `/set_timer_channel` - Set notification channel **(Admin)**"
        ),
        inline=True
    )

    # Schedule Commands
    embed.add_field(
        name="📊 **Schedule**",
        value=(
            "• `/schedule [week]` - Week matchups\n"
            "• `/find_game <team>` - Team's opponent\n"
            "• `/byes [week]` - Bye teams"
        ),
        inline=True
    )

    # League Staff
    embed.add_field(
        name="👔 **League Staff**",
        value=(
            "• `/league_staff` - View owner & co-commish\n"
            "• `/set_league_owner` - Set owner **(Admin)**\n"
            "• `/set_co_commish` - Set co-commish **(Admin)**\n"
            "• `/pick_commish [#channel]` - AI picks co-commish! 👑"
        ),
        inline=True
    )

    # Interactive Charter
    embed.add_field(
        name="📝 **Charter Updates**",
        value=(
            "• `@Harry update <rule>` - Natural language!\n"
            "• `/scan_rules #channel` - Find rule votes\n"
            "• `/charter_history` - Recent changes\n"
            "• `/charter` - Link to charter"
        ),
        inline=True
    )

    # Channel Summary
    embed.add_field(
        name="💬 **Summaries**",
        value=(
            "• `/summarize [hours] [focus]` - Summarize\n"
            "• `@Harry what happened?` - Natural!"
        ),
        inline=True
    )

    # Admin Commands
    embed.add_field(
        name="🔐 **Bot Admin**",
        value=(
            "• `/add_bot_admin` `/remove_bot_admin`\n"
            "• `/list_bot_admins`\n"
            "• `/block_channel` `/unblock_channel`"
        ),
        inline=True
    )

    # Version Info
    embed.add_field(
        name="ℹ️ **Info**",
        value=(
            "• `/whats_new` - Latest features\n"
            "• `/version` - Bot version\n"
            "• `/changelog` - Version history"
        ),
        inline=True
    )

    embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈 | @Harry works anywhere!")

    # Admin Management Commands
    embed.add_field(
        name="🔐 **Admin Management**",
        value=(
            "• `/add_bot_admin @user` - Add bot admin **(Admin only)**\n"
            "• `/remove_bot_admin @user` - Remove bot admin **(Admin only)**\n"
            "• `/list_bot_admins` - List all bot admins"
        ),
        inline=False
    )

    # Channel Management Commands
    embed.add_field(
        name="🔇 **Channel Management (Admin Only)**",
        value=(
            "• `/block_channel #channel` - Block unprompted responses\n"
            "• `/unblock_channel #channel` - Allow unprompted responses\n"
            "• `/list_blocked_channels` - Show blocked channels\n"
            "\n*Note: @mentions still work in blocked channels!*"
        ),
        inline=False
    )

    embed.add_field(
        name="💬 **Chat Interactions**",
        value=(
            "• Mention me: `@Harry what are the rules?`\n"
            "• Ask questions: `What's the transfer policy?`\n"
            "• Say hi: `Hi Harry!`\n"
            "• React with ❓ to my messages for help"
        ),
        inline=False
    )

    embed.add_field(
        name="📖 **OFFICIAL LEAGUE CHARTER**",
        value="[**📋 View Complete Rules & Policies**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)\n\n*This is the official source for all CFB 26 league rules!*",
        inline=False
    )

    embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈 | Ready to help!")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="tokens", description="Show AI token usage statistics")
async def show_tokens(interaction: discord.Interaction):
    """Show AI token usage statistics"""
    if AI_AVAILABLE and ai_assistant:
        stats = ai_assistant.get_token_usage()
        embed = discord.Embed(
            title="🔢 AI Token Usage Statistics",
            color=0x00ff00
        )

        embed.add_field(
            name="📊 Usage Summary",
            value=f"**Total Requests:** {stats['total_requests']}\n**OpenAI Tokens:** {stats['openai_tokens']:,}\n**Anthropic Tokens:** {stats['anthropic_tokens']:,}\n**Total Tokens:** {stats['total_tokens']:,}",
            inline=False
        )

        if stats['total_requests'] > 0:
            avg_tokens = stats['total_tokens'] / stats['total_requests']
            embed.add_field(
                name="📈 Averages",
                value=f"**Avg Tokens per Request:** {avg_tokens:.1f}",
                inline=False
            )

        # Add cost estimates (rough approximations)
        openai_cost = stats['openai_tokens'] * 0.000002  # GPT-3.5-turbo pricing
        embed.add_field(
            name="💰 Estimated Costs",
            value=f"**OpenAI Cost:** ~${openai_cost:.4f}\n**Note:** Actual costs may vary based on model and pricing",
            inline=False
        )

        embed.set_footer(text="Token usage since bot startup")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ AI integration not available")

@bot.tree.command(name="search", description="Search the official league charter")
async def search_charter(interaction: discord.Interaction, search_term: str):
    """Search for specific terms in the league charter"""
    await interaction.response.send_message("🔍 Searching...", ephemeral=True)

    embed = discord.Embed(
        title=f"🔍 Search Results: '{search_term}'",
        color=0xffa500
    )

    if GOOGLE_DOCS_AVAILABLE and google_docs:
        try:
            results = google_docs.search_document(search_term)
            if results:
                embed.description = "Found in the league charter:"
                for i, result in enumerate(results, 1):
                    # Truncate long results
                    if len(result) > 200:
                        result = result[:200] + "..."
                    embed.add_field(
                        name=f"Result {i}",
                        value=result,
                        inline=False
                    )
            else:
                embed.description = "No results found in the charter."
        except Exception as e:
            embed.description = f"Error searching charter: {str(e)}"
    else:
        embed.description = "Google Docs integration not available. Use the direct link to search manually."

    embed.add_field(
        name="📖 Full Charter",
        value="[Open League Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="player", description="Look up a college football player's stats and info")
async def lookup_player(
    interaction: discord.Interaction,
    name: str,
    team: str = None
):
    """
    Look up player info from CollegeFootballData.com

    Args:
        name: Player name to search for (e.g., "James Smith")
        team: Optional team name to filter results (e.g., "Alabama")
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ Player lookup is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    logger.info(f"🏈 /player command from {interaction.user}: {name}" + (f" from {team}" if team else ""))

    try:
        player_info = await player_lookup.get_full_player_info(name, team)

        if player_info:
            response = player_lookup.format_player_response(player_info)
            embed = discord.Embed(
                title="🏈 Player Info",
                description=response,
                color=0x1e90ff
            )

            # Check if it's an Oregon player and add snark (Harry always hates Oregon)
            player_team = player_info.get('player', {}).get('team', '').lower()
            if 'oregon' in player_team and 'oregon state' not in player_team:
                embed.set_footer(text="Harry's Player Lookup 🏈 | Though why you'd care about a Duck is beyond me...")
            else:
                embed.set_footer(text="Harry's Player Lookup 🏈 | Data from CollegeFootballData.com")

            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❓ Player Not Found",
                description=f"Couldn't find a player matching **{name}**" + (f" from **{team}**" if team else "") + ".",
                color=0xff6600
            )
            embed.add_field(
                name="💡 Tips",
                value="• Check the spelling\n• Use full name (First Last)\n• FCS/smaller schools may have limited data\n• Try without the team name",
                inline=False
            )
            embed.set_footer(text="Harry's Player Lookup 🏈 | Data from CollegeFootballData.com")
            await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /player command: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error looking up player: {str(e)}", ephemeral=True)


@bot.tree.command(name="players", description="Look up multiple players at once")
async def lookup_players_bulk(
    interaction: discord.Interaction,
    player_list: str
):
    """
    Look up multiple players at once.

    Args:
        player_list: List of players separated by commas or semicolons.
                     Format: "Name (Team Position)" or "Name, Team"
                     Example: "James Smith (Bama DT); Isaiah Horton (Bama WR)"
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    # Parse the player list
    players = player_lookup.parse_player_list(player_list)

    if not players:
        await interaction.response.send_message(
            "❌ Couldn't parse any players from that list, mate!\n\n"
            "**Supported formats:**\n"
            "• `James Smith (Bama DT)`\n"
            "• `Isaiah Horton, Alabama, WR`\n"
            "• `Dre'Lon Miller (WR Colorado)`\n\n"
            "Separate multiple players with `;` or put each on a new line.",
            ephemeral=True
        )
        return

    if len(players) > 15:
        await interaction.response.send_message(
            f"❌ That's {len(players)} players - max is 15 at a time to avoid rate limits!",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    logger.info(f"🏈 /players bulk lookup from {interaction.user}: {len(players)} players")

    try:
        results = await player_lookup.lookup_multiple_players(players)
        response = player_lookup.format_bulk_player_response(results)

        # Split into multiple messages if too long
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title="🏈 Player Lookup Results" + (f" (Part {i+1})" if len(chunks) > 1 else ""),
                    description=chunk,
                    color=0x1e90ff
                )
                if i == len(chunks) - 1:
                    embed.set_footer(text="Harry's Bulk Lookup 🏈 | Data from CollegeFootballData.com")
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🏈 Player Lookup Results",
                description=response,
                color=0x1e90ff
            )
            embed.set_footer(text="Harry's Bulk Lookup 🏈 | Data from CollegeFootballData.com")
            await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /players command: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error looking up players: {str(e)}", ephemeral=True)


@bot.tree.command(name="rankings", description="Get college football rankings (AP, Coaches, CFP)")
async def get_rankings(
    interaction: discord.Interaction,
    team: str = None,
    year: int = 2025
):
    """
    Get CFB rankings - optionally filter by team

    Args:
        team: Optional team to check ranking for
        year: Year to check (default: 2025)
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        if team:
            result = await player_lookup.get_team_ranking(team, year)
            response = player_lookup.format_team_ranking(result)
            title = f"📊 {team} Rankings ({year})"
        else:
            result = await player_lookup.get_rankings(year)
            response = player_lookup.format_rankings(result)
            title = f"📊 College Football Rankings ({year})"

        embed = discord.Embed(title=title, description=response, color=0x1e90ff)
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /rankings: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="matchup", description="Get historical matchup data between two teams")
async def get_matchup(
    interaction: discord.Interaction,
    team1: str,
    team2: str
):
    """
    Get all-time matchup history between two teams

    Args:
        team1: First team (e.g., "Alabama")
        team2: Second team (e.g., "Auburn")
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await player_lookup.get_matchup_history(team1, team2)
        response = player_lookup.format_matchup(result)

        embed = discord.Embed(
            title=f"🏈 {team1} vs {team2}",
            description=response,
            color=0x1e90ff
        )
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /matchup: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="cfb_schedule", description="Get a team's schedule and results")
async def get_cfb_schedule(
    interaction: discord.Interaction,
    team: str,
    year: int = 2025
):
    """
    Get a team's full schedule for a season

    Args:
        team: Team name (e.g., "Nebraska")
        year: Season year (default: 2025)
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await player_lookup.get_team_schedule(team, year)
        response = player_lookup.format_schedule(result, team)

        embed = discord.Embed(
            title=f"📅 {team} Schedule ({year})",
            description=response,
            color=0x1e90ff
        )
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /cfb_schedule: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="draft_picks", description="Get NFL draft picks from a college")
async def get_draft_picks(
    interaction: discord.Interaction,
    team: str = None,
    year: int = 2025
):
    """
    Get NFL draft picks, optionally filtered by college

    Args:
        team: Optional college team to filter by
        year: Draft year (default: 2025)
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await player_lookup.get_draft_picks(team, year)
        response = player_lookup.format_draft_picks(result, team)

        title = f"🏈 {year} NFL Draft Picks" + (f" from {team}" if team else "")
        embed = discord.Embed(title=title, description=response, color=0x1e90ff)
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /draft_picks: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="transfers", description="Get transfer portal activity for a team")
async def get_transfers(
    interaction: discord.Interaction,
    team: str,
    year: int = 2025
):
    """
    Get transfer portal incoming and outgoing for a team

    Args:
        team: Team name (e.g., "USC")
        year: Year to check (default: 2025)
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await player_lookup.get_team_transfers(team, year)
        response = player_lookup.format_transfers(result, team)

        embed = discord.Embed(
            title=f"🔄 {team} Transfer Portal ({year})",
            description=response,
            color=0x1e90ff
        )
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /transfers: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="betting", description="Get betting lines for games")
async def get_betting(
    interaction: discord.Interaction,
    team: str = None,
    year: int = 2025,
    week: int = None
):
    """
    Get betting lines for games

    Args:
        team: Optional team to filter by
        year: Season year (default: 2025)
        week: Optional week number
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await player_lookup.get_betting_lines(team, year, week)
        response = player_lookup.format_betting_lines(result)

        title = "💰 Betting Lines"
        if team:
            title += f" - {team}"
        if week:
            title += f" (Week {week})"

        embed = discord.Embed(title=title, description=response, color=0x1e90ff)
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /betting: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="team_ratings", description="Get advanced ratings (SP+, SRS, Elo) for a team")
async def get_team_ratings(
    interaction: discord.Interaction,
    team: str,
    year: int = 2025
):
    """
    Get advanced analytics ratings for a team

    Args:
        team: Team name (e.g., "Ohio State")
        year: Season year (default: 2025)
    """
    if not await check_module_enabled(interaction, FeatureModule.CFB_DATA):
        return

    if not player_lookup.is_available:
        await interaction.response.send_message(
            "❌ CFB data is not configured. CFB_DATA_API_KEY is missing.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        result = await player_lookup.get_team_ratings(team, year)
        response = player_lookup.format_ratings(result)

        embed = discord.Embed(
            title=f"📈 {team} Advanced Ratings ({year})",
            description=response,
            color=0x1e90ff
        )
        embed.set_footer(text="Harry's CFB Data 🏈 | Data from CollegeFootballData.com")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        logger.error(f"❌ Error in /team_ratings: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="harry", description="Ask Harry (the bot) about league rules and policies")
async def ask_harry(interaction: discord.Interaction, question: str):
    """Ask Harry (the bot) about the league charter in a conversational way"""
    embed = discord.Embed(
        title="🏈 Harry's Response",
        color=0x1e90ff
    )

    if AI_AVAILABLE and ai_assistant:
        try:
            # Send initial response immediately
            await interaction.response.send_message("🤔 Harry is thinking...", ephemeral=True)

            # Log the slash command usage
            guild_name = interaction.guild.name if interaction.guild else "DM"
            logger.info(f"🎯 SLASH COMMAND: /harry from {interaction.user} ({interaction.user.id}) in {guild_name} - '{question}'")
            logger.info(f"🔍 Slash command question: '{question}'")
            logger.info(f"🏠 Server: {guild_name} (ID: {interaction.guild.id if interaction.guild else 'DM'})")

            # Classification for slash commands
            is_question, league_related, matched_keywords = classify_question(question)

            logger.info(f"🔍 CLASSIFICATION: is_question={is_question}, league_related={league_related}")
            if league_related:
                logger.info(f"🎯 Matched keywords: {matched_keywords}")

            # Get personality based on server settings
            cmd_guild_id = interaction.guild.id if interaction.guild else 0
            personality = server_config.get_personality_prompt(cmd_guild_id)

            # Make the AI response more conversational
            conversational_question = f"{personality} Answer this question about CFB 26 league rules: {question}"
            response = await ai_assistant.ask_ai(conversational_question, f"{interaction.user} ({interaction.user.id})")

            if response:
                embed.description = response
                embed.add_field(
                    name="💬 Responding to:",
                    value=f"*{question}*",
                    inline=False
                )
                embed.add_field(
                    name="💡 Need More Info?",
                    value="Ask me anything about league rules, or check the full charter below!",
                    inline=False
                )
            else:
                embed.description = "Sorry, I couldn't get a response right now. Let me check the charter for you!"
                embed.add_field(
                    name="💬 Responding to:",
                    value=f"*{question}*",
                    inline=False
                )
        except Exception as e:
            embed.description = f"Oops! Something went wrong: {str(e)}"
            embed.add_field(
                name="💬 Responding to:",
                value=f"*{question}*",
                inline=False
            )
    else:
        embed.description = "Hi! I'm Harry, your CFB 26 league assistant. I'm having some technical difficulties right now, but you can always check the charter directly!"
        embed.add_field(
            name="💬 Responding to:",
            value=f"*{question}*",
            inline=False
        )

    embed.add_field(
        name="📖 Full League Charter",
        value="[Open Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")

    # Send the actual response
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ask", description="Ask Harry general questions (not league-specific)")
async def ask_ai(interaction: discord.Interaction, question: str):
    """Ask AI general questions (use /harry for league-specific questions)"""
    embed = discord.Embed(
        title="🤖 AI Assistant Response",
        color=0x9b59b6
    )

    response_sent = False

    try:
        # Send initial response immediately
        await interaction.response.send_message("🤖 Thinking...", ephemeral=True)
        response_sent = True

        # Log the slash command usage
        guild_name = interaction.guild.name if interaction.guild else "DM"
        logger.info(f"🎯 SLASH COMMAND: /ask from {interaction.user} ({interaction.user.id}) in {guild_name} - '{question}'")
        logger.info(f"🔍 Slash command question: '{question}'")
        logger.info(f"🏠 Server: {guild_name} (ID: {interaction.guild.id if interaction.guild else 'DM'})")

        if not AI_AVAILABLE or not ai_assistant:
            embed.description = "AI integration not available. Please check the charter directly or use other commands."
        else:
            # Get personality based on server settings
            ask_guild_id = interaction.guild.id if interaction.guild else 0
            personality = server_config.get_personality_prompt(ask_guild_id)

            # Add Harry's personality to the ask command
            harry_question = f"{personality} Answer this question: {question}"

            # /ask ALWAYS uses general AI without charter context (not league-specific)
            logger.info("🌍 /ask command - ALWAYS using general AI without charter context")
            general_context = personality

            # Call OpenAI directly with general context
            logger.info("🔄 Attempting OpenAI API call...")
            response = await ai_assistant.ask_openai(harry_question, general_context, personality_prompt=personality)
            if not response:
                # Fallback to Anthropic
                logger.info("⚠️ OpenAI failed, attempting Anthropic fallback...")
                response = await ai_assistant.ask_anthropic(harry_question, general_context, personality_prompt=personality)

            if response:
                logger.info(f"✅ AI response received ({len(response)} characters)")
                embed.description = response
                embed.add_field(
                    name="💡 Note",
                    value="This is a general question. For league-specific questions, use `/harry` instead!",
                    inline=False
                )
            else:
                logger.error("❌ Both OpenAI and Anthropic failed to respond")
                embed.description = "Sorry, I couldn't get an AI response right now. Both OpenAI and Anthropic APIs failed. Check your API keys or try again later!"
                embed.add_field(
                    name="🔧 Troubleshooting",
                    value="Make sure OPENAI_API_KEY or ANTHROPIC_API_KEY is set in your environment variables.",
                    inline=False
                )
    except Exception as e:
        logger.error(f"❌ Exception in /ask command: {str(e)}", exc_info=True)
        if not response_sent:
            # If we haven't sent a response yet, send it as the initial response
            try:
                embed.description = f"Error getting AI response: {str(e)}"
                embed.add_field(
                    name="🔍 Error Details",
                    value=f"Check the logs for more information. Error type: {type(e).__name__}",
                    inline=False
                )
                await interaction.response.send_message(embed=embed)
                return
            except discord.errors.InteractionResponded:
                pass  # Already responded, try followup
        else:
            # Already sent initial response, use followup
            embed.description = f"Error getting AI response: {str(e)}"
            embed.add_field(
                name="🔍 Error Details",
                value=f"Check the logs for more information. Error type: {type(e).__name__}",
                inline=False
            )

    # Add charter link (always)
    embed.add_field(
        name="📖 Full Charter",
        value="[Open League Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    embed.set_footer(text="CFB 26 League Bot - AI Assistant")

    # Send the actual response
    if response_sent:
        await interaction.followup.send(embed=embed)
    else:
        # Fallback: send as initial response if something went wrong
        try:
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"❌ Failed to send /ask response: {str(e)}", exc_info=True)

@bot.tree.command(name="advance", description="Start advance countdown timer (Admin only)")
async def start_advance(interaction: discord.Interaction, hours: int = 48):
    """
    Start the advance countdown timer

    Args:
        hours: Number of hours for the countdown (default: 48)
    """
    # Check if league module is enabled
    if not await check_module_enabled(interaction, FeatureModule.LEAGUE):
        return

    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to start countdowns, ya muppet!", ephemeral=True)
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    # Validate hours (minimum 1, maximum 336 = 2 weeks)
    if hours < 1:
        await interaction.response.send_message("❌ Hours must be at least 1, ya numpty!", ephemeral=True)
        return
    if hours > 336:
        await interaction.response.send_message("❌ Maximum is 336 hours (2 weeks), mate!", ephemeral=True)
        return

    # Defer immediately - this operation takes time (stop timer, increment week, start timer, DM updates)
    try:
        await interaction.response.defer()
    except Exception as e:
        logger.error(f"Failed to defer /advance interaction: {e}")
        return

    # Stop existing timer if one is running (manual advance)
    status = timekeeper_manager.get_status(interaction.channel)
    if status.get('active'):
        logger.info(f"⏹️ Stopping existing timer before manual /advance")
        await timekeeper_manager.stop_timer(interaction.channel)

    # Increment the week (manual advance)
    season_info = timekeeper_manager.get_season_week()
    if season_info['season'] and season_info['week'] is not None:
        old_week = season_info['week']
        old_week_name = season_info.get('week_name', f"Week {old_week}")
        await timekeeper_manager.increment_week()
        # Refresh season_info after increment
        season_info = timekeeper_manager.get_season_week()
        new_week_name = season_info.get('week_name', f"Week {season_info['week']}")
        logger.info(f"📅 Manual /advance: {old_week_name} → {new_week_name}")

    # Start the countdown
    success = await timekeeper_manager.start_timer(interaction.channel, hours)

    if success:
        # Get season/week info for display (already refreshed above if incremented)
        if not season_info:
            season_info = timekeeper_manager.get_season_week()
        if season_info['season'] and season_info['week'] is not None:
            week_name = season_info.get('week_name', f"Week {season_info['week']}")
            next_week_name = get_week_name(season_info['week'] + 1)
            phase = season_info.get('phase', 'Regular Season')
            season_text = f"**Season {season_info['season']}**\n📍 {week_name} → **{next_week_name}**\n🏈 Phase: {phase}\n\n"
        else:
            season_text = ""

        embed = discord.Embed(
            title="⏰ Advance Countdown Started!",
            description=f"Right then, listen up ya wankers!\n\n🏈 **{hours} HOUR COUNTDOWN STARTED** 🏈\n\n{season_text}You got **{hours} hours** to get your bleedin' games done!\n\nI'll be remindin' you lot at:\n• 24 hours remaining (if applicable)\n• 12 hours remaining (if applicable)\n• 6 hours remaining (if applicable)\n• 1 hour remaining\n\nAnd when time's up... well, you'll know! 😈",
            color=0x00ff00
        )
        status = timekeeper_manager.get_status(interaction.channel)
        embed.add_field(
            name="⏳ Deadline",
            value=format_est_time(status['end_time'], '%A, %B %d at %I:%M %p'),
            inline=False
        )
        embed.set_footer(text="Harry's Advance Timer 🏈 | Use /time_status to check progress")

        # Send ephemeral confirmation to admin
        await interaction.followup.send("✅ Timer started! Announcement sent to #general.", ephemeral=True)

        # Send public announcement to #general
        notification_channel = get_notification_channel()
        if notification_channel:
            await notification_channel.send(content="@everyone", embed=embed)
            logger.info(f"⏰ Advance countdown started by {interaction.user} - {hours} hours - announced in #{notification_channel.name}")

            # Send schedule for the current week
            if season_info and season_info.get('week') is not None:
                await send_week_schedule(notification_channel, season_info['week'])
        else:
            # Fallback to current channel if #general not found
            await interaction.channel.send(content="@everyone", embed=embed)
            logger.warning(f"⚠️ #general not found, announced in {interaction.channel}")
    else:
        embed = discord.Embed(
            title="❌ Failed to Start Countdown!",
            description="Blimey, something went wrong starting the timer, mate!",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="time_status", description="Check the current advance countdown status")
async def check_time_status(interaction: discord.Interaction):
    """Check the current advance countdown status"""
    # Check if league module is enabled
    if not await check_module_enabled(interaction, FeatureModule.LEAGUE):
        return

    # Defer immediately to prevent timeout
    try:
        await interaction.response.defer()
    except discord.errors.InteractionResponded:
        # Already responded, continue with followup
        pass

    if not timekeeper_manager:
        await interaction.followup.send("❌ Timekeeper not available", ephemeral=True)
        return

    try:
        status = timekeeper_manager.get_status(interaction.channel)

        if not status['active']:
            embed = discord.Embed(
                title="⏰ No Countdown Active",
                description="There ain't no countdown runnin' right now, mate.\n\nUse `/advance` to start the 48-hour countdown.",
                color=0x808080
            )
            await interaction.followup.send(embed=embed)
        else:
            hours = status['hours']
            minutes = status['minutes']

            # Determine urgency color
            if hours >= 24:
                color = 0x00ff00  # Green
                urgency = "Loads of time, but still play your fucking games!"
            elif hours >= 12:
                color = 0xffa500  # Orange
                urgency = "Getting closer now, better get crackin'!"
            elif hours >= 6:
                color = 0xff8c00  # Dark orange
                urgency = "Time's tickin' away! Get your games done!"
            elif hours >= 1:
                color = 0xff4500  # Red orange
                urgency = "BLOODY HELL! Time's almost up!"
            else:
                color = 0xff0000  # Red
                urgency = "LAST HOUR! GET MOVIN'!"

            # Get season/week info
            season_info = timekeeper_manager.get_season_week()
            season_text = ""
            if season_info['season'] and season_info['week'] is not None:
                week_name = season_info.get('week_name', f"Week {season_info['week']}")
                current_week = season_info['week']

                # Check if we're at Preseason (Week 29) - next advance starts new season!
                if current_week >= TOTAL_WEEKS_PER_SEASON - 1:
                    next_season = season_info['season'] + 1
                    season_text = f"\n\n🎉 **LAST WEEK OF SEASON {season_info['season']}!** 🎉\n"
                    season_text += f"📍 {week_name} → **Season {next_season}, Week 0 - Season Kickoff**\n"
                    season_text += f"🏈 Next advance starts a NEW SEASON!"
                else:
                    next_week = current_week + 1
                    next_week_info = get_week_info(next_week)
                    next_week_name = next_week_info["name"]
                    next_phase = next_week_info["phase"]
                    next_actions = next_week_info.get("actions", "")
                    next_notes = next_week_info.get("notes", "")

                    season_text = f"\n\n**Season {season_info['season']}**\n📍 {week_name} → **{next_week_name}**\n🏈 Phase: {next_phase}"
                    if next_actions:
                        season_text += f"\n\n📋 **Next Week Actions:**\n{next_actions}"
                    if next_notes:
                        season_text += f"\n⚠️ {next_notes}"

            embed = discord.Embed(
                title="⏰ Advance Countdown Status",
                description=f"**Time Remaining:** {hours}h {minutes}m\n\n{urgency}{season_text}",
                color=color
            )

            embed.add_field(
                name="📅 Started",
                value=format_est_time(status['start_time'], '%I:%M %p on %B %d'),
                inline=True
            )
            embed.add_field(
                name="⏳ Deadline",
                value=format_est_time(status['end_time'], '%I:%M %p on %B %d'),
                inline=True
            )

            # Add progress bar
            timer = timekeeper_manager.get_timer(interaction.channel)
            if timer:
                total_seconds = timer.duration_hours * 3600
                remaining_seconds = status['remaining'].total_seconds()
                progress = 1 - (remaining_seconds / total_seconds)
                bar_length = 20
                filled = int(bar_length * progress)
                bar = '█' * filled + '░' * (bar_length - filled)

                embed.add_field(
                    name="📊 Progress",
                    value=f"{bar} {int(progress * 100)}%",
                    inline=False
                )

                # Add persistence status (for verification)
                persistence_status = "✅ Persisted" if timekeeper_manager.state_message_id else "⚠️ Not persisted"
                embed.add_field(
                    name="💾 Persistence",
                    value=f"{persistence_status}\nTimer state saved to Discord for deployment survival",
                    inline=False
                )

            embed.set_footer(text="Harry's Advance Timer 🏈")
            await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Error in /time_status: {str(e)}", exc_info=True)
        await interaction.followup.send(f"❌ Error checking timer status: {str(e)}", ephemeral=True)

@bot.tree.command(name="stop_countdown", description="Stop the current advance countdown (Admin only)")
async def stop_countdown(interaction: discord.Interaction):
    """Stop the current advance countdown"""
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to stop countdowns!", ephemeral=True)
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    success = await timekeeper_manager.stop_timer(interaction.channel)

    if success:
        embed = discord.Embed(
            title="⏹️ Countdown Stopped",
            description="Right, countdown's been cancelled then!\n\nAll timers have been stopped.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Admin-only confirmation
        logger.info(f"⏹️ Countdown stopped by {interaction.user} in {interaction.channel}")
    else:
        embed = discord.Embed(
            title="❌ No Active Countdown",
            description="There ain't no countdown to stop, ya numpty!",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="week", description="Check the current season and week")
async def check_week(interaction: discord.Interaction):
    """Check the current season and week"""
    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    season_info = timekeeper_manager.get_season_week()

    if not season_info['season'] or season_info['week'] is None:
        embed = discord.Embed(
            title="📅 Season/Week Not Set",
            description="The season and week haven't been set yet, mate!\n\nAn admin needs to use `/set_season_week` to set it up.",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed)
        return

    week_name = season_info.get('week_name', f"Week {season_info['week']}")
    phase = season_info.get('phase', 'Unknown')
    week_num = season_info['week']

    # Get week details
    week_info = get_week_info(week_num)
    actions = week_info.get("actions", "")
    notes = week_info.get("notes", "")

    # Build description
    description = f"**Season {season_info['season']}**\n\n"
    description += f"📍 **{week_name}**\n"
    description += f"🏈 Phase: {phase}\n"
    description += f"📊 Week {week_num} of {TOTAL_WEEKS_PER_SEASON - 1}"

    if actions:
        description += f"\n\n📋 **Available Actions:**\n{actions}"
    if notes:
        description += f"\n\n⚠️ **Note:** {notes}"

    # Show what's next
    if week_num >= TOTAL_WEEKS_PER_SEASON - 1:
        description += f"\n\n🎉 **Next:** Season {season_info['season'] + 1}, Week 0 - Season Kickoff!"
    else:
        next_week_info = get_week_info(week_num + 1)
        description += f"\n\n➡️ **Next:** {next_week_info['name']}"

    embed = discord.Embed(
        title="📅 Current Week",
        description=description,
        color=0x00ff00
    )
    embed.set_footer(text="Harry's Week Tracker 🏈 | Use /set_season_week to change")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="weeks", description="View the full CFB 26 Dynasty week schedule")
async def view_weeks(interaction: discord.Interaction):
    """View the full week schedule for a CFB 26 Dynasty season"""
    # Get current week info
    current_week = None
    current_season = None
    if timekeeper_manager:
        season_info = timekeeper_manager.get_season_week()
        if season_info['week'] is not None:
            current_week = season_info['week']
            current_season = season_info['season']

    # Build description with current/next week at the top
    description = ""

    if current_week is not None and current_season is not None:
        # Current week info
        current_info = get_week_info(current_week)
        current_actions = current_info.get("actions", "")
        current_notes = current_info.get("notes", "")

        description += f"**Season {current_season}**\n\n"
        description += f"📍 **Current Week:** {current_info['name']}\n"
        description += f"🏈 Phase: {current_info['phase']}\n"
        if current_actions:
            description += f"📋 Actions: {current_actions}\n"
        if current_notes:
            description += f"⚠️ {current_notes}\n"

        # Next week info
        if current_week >= TOTAL_WEEKS_PER_SEASON - 1:
            description += f"\n➡️ **Next Week:** Season {current_season + 1}, Week 0 - Season Kickoff\n"
            description += f"🏈 Phase: Regular Season\n"
            description += f"📋 Actions: Season begins\n"
        else:
            next_week = current_week + 1
            next_info = get_week_info(next_week)
            next_actions = next_info.get("actions", "")
            next_notes = next_info.get("notes", "")

            description += f"\n➡️ **Next Week:** {next_info['name']}\n"
            description += f"🏈 Phase: {next_info['phase']}\n"
            if next_actions:
                description += f"📋 Actions: {next_actions}\n"
            if next_notes:
                description += f"⚠️ {next_notes}\n"

        description += "\n───────────────────────\n"
    else:
        description += "*Season/week not set. Use `/set_season_week` to set it.*\n\n"

    description += "**Full Week Schedule:**\n"

    # Create embed
    embed = discord.Embed(
        title="📅 CFB 26 Dynasty Week Schedule",
        description=description,
        color=0x00ff00
    )

    # Build the week lists by phase
    regular_season = []
    post_season = []
    offseason = []

    for week_num in sorted(CFB_DYNASTY_WEEKS.keys()):
        week_data = CFB_DYNASTY_WEEKS[week_num]
        phase = week_data["phase"]
        name = week_data["short"]  # Use short name for the list

        # Add marker if this is the current week
        if current_week is not None and week_num == current_week:
            line = f"**► `{week_num:2d}` {name}** ◄"
        else:
            line = f"`{week_num:2d}` {name}"

        if phase == "Regular Season":
            regular_season.append(line)
        elif phase == "Post-Season":
            post_season.append(line)
        else:
            offseason.append(line)

    # Regular Season field
    embed.add_field(
        name="🏈 Regular Season",
        value="\n".join(regular_season),
        inline=True
    )

    # Post-Season field
    embed.add_field(
        name="🏆 Post-Season",
        value="\n".join(post_season),
        inline=True
    )

    # Offseason field
    embed.add_field(
        name="📝 Offseason",
        value="\n".join(offseason),
        inline=True
    )

    embed.set_footer(text="Harry's Week Tracker 🏈 | Use /week for more details")
    await interaction.response.send_message(embed=embed)

# ==================== Schedule Commands ====================

@bot.tree.command(name="schedule", description="View the schedule for a specific week")
@discord.app_commands.describe(
    week="Week number (0-13 for regular season, leave empty for current week)"
)
async def view_schedule(interaction: discord.Interaction, week: Optional[int] = None):
    """View the schedule for a specific week"""
    # Check if league module is enabled
    if not await check_module_enabled(interaction, FeatureModule.LEAGUE):
        return

    if not schedule_manager:
        await interaction.response.send_message("❌ Schedule manager not available", ephemeral=True)
        return

    # If no week specified, use current week
    if week is None:
        if timekeeper_manager:
            season_info = timekeeper_manager.get_season_week()
            if season_info['week'] is not None and season_info['week'] <= 13:
                week = season_info['week']
            else:
                await interaction.response.send_message(
                    "❌ No week specified and current week is not in regular season. Use `/schedule week:X`",
                    ephemeral=True
                )
                return
        else:
            await interaction.response.send_message(
                "❌ No week specified. Use `/schedule week:X`",
                ephemeral=True
            )
            return

    # Validate week
    if week < 0 or week > 13:
        await interaction.response.send_message(
            "❌ Week must be between 0 and 13 (regular season), ya numpty!",
            ephemeral=True
        )
        return

    week_data = schedule_manager.get_week_schedule(week)
    if not week_data:
        await interaction.response.send_message(
            f"❌ No schedule data for Week {week}",
            ephemeral=True
        )
        return

    # Build embed
    embed = discord.Embed(
        title=f"📅 Week {week} Schedule",
        description=f"Season {schedule_manager.season} matchups:",
        color=0x00ff00
    )

    # Bye teams (bold user teams)
    bye_teams = week_data.get('bye_teams', [])
    if bye_teams:
        embed.add_field(
            name="🛋️ Bye Week",
            value=schedule_manager.format_bye_teams(bye_teams),
            inline=False
        )

    # Games (bold user teams)
    games = week_data.get('games', [])
    if games:
        games_text = "\n".join([schedule_manager.format_game(g, "•") for g in games])
        embed.add_field(
            name="🏈 Games",
            value=games_text,
            inline=False
        )

    embed.set_footer(text="Harry's Schedule Tracker 🏈 | Use /find_game for specific team info")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="find_game", description="Find a team's game for a specific week")
@discord.app_commands.describe(
    team="Team name (e.g., Hawaii, LSU, Notre Dame)",
    week="Week number (0-13, leave empty for current week)"
)
async def find_game(interaction: discord.Interaction, team: str, week: Optional[int] = None):
    """Find a specific team's game in the dynasty schedule"""
    if not schedule_manager:
        await interaction.response.send_message("❌ Schedule manager not available", ephemeral=True)
        return

    # If no week specified, use current week
    if week is None:
        if timekeeper_manager:
            season_info = timekeeper_manager.get_season_week()
            if season_info['week'] is not None and season_info['week'] <= 13:
                week = season_info['week']
            else:
                await interaction.response.send_message(
                    "❌ No week specified and current week is not in regular season. Use `/find_game team:X week:Y`",
                    ephemeral=True
                )
                return
        else:
            await interaction.response.send_message(
                "❌ No week specified. Use `/find_game team:X week:Y`",
                ephemeral=True
            )
            return

    # Find the team
    found_team = schedule_manager.find_team(team)
    if not found_team:
        await interaction.response.send_message(
            f"❌ Couldn't find team '{team}'. Available teams: {', '.join(schedule_manager.teams)}",
            ephemeral=True
        )
        return

    # Get the game
    game = schedule_manager.get_team_game(found_team, week)
    if not game:
        await interaction.response.send_message(
            f"❌ No game data for {found_team} in Week {week}",
            ephemeral=True
        )
        return

    if game.get('bye'):
        embed = discord.Embed(
            title=f"🛋️ {found_team} - Week {week}",
            description=f"**{found_team}** has a bye week!\n\nTime to rest up and prepare for the next game.",
            color=0x808080
        )
    else:
        location_emoji = "🏠" if game['location'] == 'home' else "✈️"
        location_text = "HOME" if game['location'] == 'home' else "AWAY"

        embed = discord.Embed(
            title=f"🏈 {found_team} - Week {week}",
            description=f"**{game['matchup']}**",
            color=0x00ff00
        )
        embed.add_field(
            name="Opponent",
            value=game['opponent'],
            inline=True
        )
        embed.add_field(
            name=f"{location_emoji} Location",
            value=location_text,
            inline=True
        )

    embed.set_footer(text="Harry's Schedule Tracker 🏈")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="byes", description="Show which teams have a bye this week")
@discord.app_commands.describe(
    week="Week number (0-13, leave empty for current week)"
)
async def view_byes(interaction: discord.Interaction, week: Optional[int] = None):
    """Show teams on bye for a specific week"""
    if not schedule_manager:
        await interaction.response.send_message("❌ Schedule manager not available", ephemeral=True)
        return

    # If no week specified, use current week
    if week is None:
        if timekeeper_manager:
            season_info = timekeeper_manager.get_season_week()
            if season_info['week'] is not None and season_info['week'] <= 13:
                week = season_info['week']
            else:
                await interaction.response.send_message(
                    "❌ No week specified and current week is not in regular season.",
                    ephemeral=True
                )
                return
        else:
            await interaction.response.send_message("❌ No week specified.", ephemeral=True)
            return

    bye_teams = schedule_manager.get_bye_teams(week)

    if bye_teams:
        embed = discord.Embed(
            title=f"🛋️ Week {week} Bye Teams",
            description=f"These lucky sods get a week off:\n\n**{', '.join(bye_teams)}**",
            color=0x808080
        )
    else:
        embed = discord.Embed(
            title=f"🏈 Week {week} - No Byes!",
            description="Everyone's playing this week! No rest for the wicked!",
            color=0x00ff00
        )

    embed.set_footer(text="Harry's Schedule Tracker 🏈")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="set_season_week", description="Set the current season and week (Admin only)")
async def set_season_week(interaction: discord.Interaction, season: int, week: int):
    """Set the current season and week"""
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to set season/week, ya muppet!", ephemeral=True)
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    # Validate inputs
    if season < 1:
        await interaction.response.send_message("❌ Season must be at least 1, ya numpty!", ephemeral=True)
        return
    if week < 0:
        await interaction.response.send_message("❌ Week must be at least 0, ya numpty!", ephemeral=True)
        return

    # Set season/week
    success = await timekeeper_manager.set_season_week(season, week)

    if success:
        week_info = get_week_info(week)
        week_name = week_info["name"]
        phase = week_info["phase"]
        actions = week_info.get("actions", "")
        notes = week_info.get("notes", "")

        description = f"Right then! Season and week have been set.\n\n**Season {season}**\n📍 **{week_name}**\n🏈 Phase: {phase}"
        if actions:
            description += f"\n\n📋 **Actions Available:**\n{actions}"
        if notes:
            description += f"\n\n⚠️ **Note:** {notes}"
        description += "\n\nThe week will automatically increment when the advance timer completes!"

        embed = discord.Embed(
            title="📅 Season/Week Set!",
            description=description,
            color=0x00ff00
        )
        embed.set_footer(text="Harry's Advance Timer 🏈 | Week will increment on advance")
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Admin-only confirmation
        logger.info(f"📅 Season/Week set to Season {season}, {week_name} by {interaction.user}")
    else:
        embed = discord.Embed(
            title="❌ Failed to Set Season/Week",
            description="Couldn't set the season/week, mate. Check your inputs!",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="set_timer_channel", description="Set the channel for timer notifications (Admin only)")
async def set_timer_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """Set the channel where timer notifications (advance announcements, countdowns) will be sent"""
    global GENERAL_CHANNEL_ID

    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to set the timer channel, ya muppet!", ephemeral=True)
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    # Update the channel ID and persist it
    success = await timekeeper_manager.set_notification_channel(channel.id)
    if success:
        GENERAL_CHANNEL_ID = channel.id  # Also update the module-level constant

        embed = discord.Embed(
            title="📢 Timer Notification Channel Set!",
            description=f"Right then! All timer notifications will now go to:\n\n**#{channel.name}** (<#{channel.id}>)\n\nThis includes:\n• Advance countdown start\n• 24h/12h/6h/1h warnings\n• TIME'S UP announcements\n• Schedule updates\n\n✅ **Saved!** This will persist across bot restarts.",
            color=0x00ff00
        )
        embed.set_footer(text="Harry's Advance Timer 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Admin-only confirmation
        logger.info(f"📢 Timer notification channel set to #{channel.name} by {interaction.user}")
    else:
        await interaction.response.send_message("❌ Failed to save the timer channel setting!", ephemeral=True)

# ==================== League Staff Commands ====================

@bot.tree.command(name="league_staff", description="View the current league owner and co-commissioner")
async def view_league_staff(interaction: discord.Interaction):
    """View current league staff"""
    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    staff = timekeeper_manager.get_league_staff()

    # Build the embed
    owner_text = f"<@{staff['owner_id']}>" if staff['owner_id'] else "Not set"

    if staff['co_commish_name'] == timekeeper_manager.NO_CO_COMMISH:
        co_commish_text = f"😤 {timekeeper_manager.NO_CO_COMMISH}"
    elif staff['co_commish_id']:
        co_commish_text = f"<@{staff['co_commish_id']}>"
    else:
        co_commish_text = "Not set"

    embed = discord.Embed(
        title="👑 League Staff",
        description="The brave souls running this circus...",
        color=0xffd700  # Gold
    )
    embed.add_field(
        name="🏆 League Owner",
        value=owner_text,
        inline=False
    )
    embed.add_field(
        name="👤 Co-Commissioner",
        value=co_commish_text,
        inline=False
    )
    embed.set_footer(text="Harry's League Tracker 🏈 | Admins use /set_league_owner and /set_co_commish")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="set_league_owner", description="Set the league owner (Admin only)")
async def set_league_owner(interaction: discord.Interaction, user: discord.User):
    """Set the league owner"""
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to set the league owner, ya muppet!", ephemeral=True)
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    success = await timekeeper_manager.set_league_owner(user)

    if success:
        embed = discord.Embed(
            title="👑 League Owner Set!",
            description=f"All hail the new boss!\n\n**League Owner:** <@{user.id}>\n\nMay their reign be glorious (or at least not completely shite)!",
            color=0xffd700
        )
        embed.set_footer(text="Harry's League Tracker 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Admin-only confirmation
        logger.info(f"👑 League owner set to {user.display_name} by {interaction.user}")
    else:
        await interaction.response.send_message("❌ Failed to set league owner, mate!", ephemeral=True)

@bot.tree.command(name="set_co_commish", description="Set the co-commissioner (Admin only)")
@discord.app_commands.describe(
    user="The user to set as co-commissioner (leave empty if setting to 'none')",
    none="Set to 'We don't fucking have one'"
)
async def set_co_commish(
    interaction: discord.Interaction,
    user: Optional[discord.User] = None,
    none: bool = False
):
    """Set the co-commissioner"""
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to set the co-commish, ya muppet!", ephemeral=True)
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    # Must specify either user or none
    if not user and not none:
        await interaction.response.send_message(
            "❌ You gotta either pick a user OR set `none` to True if you don't have a co-commish, ya numpty!",
            ephemeral=True
        )
        return

    if user and none:
        await interaction.response.send_message(
            "❌ Make up your mind! Either pick a user OR set none to True, not both!",
            ephemeral=True
        )
        return

    success = await timekeeper_manager.set_co_commish(user=user, no_co_commish=none)

    if success:
        if none:
            embed = discord.Embed(
                title="👤 Co-Commissioner Updated!",
                description=f"Right then, no co-commish it is!\n\n**Co-Commissioner:** 😤 {timekeeper_manager.NO_CO_COMMISH}\n\nThe owner's flying solo on this one!",
                color=0xff6600
            )
        else:
            embed = discord.Embed(
                title="👤 Co-Commissioner Set!",
                description=f"We've got ourselves a co-commish!\n\n**Co-Commissioner:** <@{user.id}>\n\nHope they're ready to help wrangle these muppets!",
                color=0x00ff00
            )
        embed.set_footer(text="Harry's League Tracker 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)  # Admin-only confirmation
        if none:
            logger.info(f"👤 Co-commish set to 'none' by {interaction.user}")
        else:
            logger.info(f"👤 Co-commish set to {user.display_name} by {interaction.user}")
    else:
        await interaction.response.send_message("❌ Failed to set co-commish, mate!", ephemeral=True)

@bot.tree.command(name="pick_commish", description="Harry analyzes the chat and picks a co-commissioner")
@discord.app_commands.describe(
    channel="Channel to analyze (default: current channel)",
    hours="How many hours of chat history to analyze (default: 168 = 1 week)"
)
async def pick_commish(
    interaction: discord.Interaction,
    channel: Optional[discord.TextChannel] = None,
    hours: int = 168
):
    """Have Harry analyze chat activity and recommend a co-commissioner"""
    # Defer IMMEDIATELY - this takes a while and Discord times out after 3 seconds
    await interaction.response.defer()

    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.followup.send(
            "❌ Only admins can ask me to pick a commish, ya muppet!",
            ephemeral=True
        )
        return

    # Use provided channel or fall back to current channel
    target_channel = channel or interaction.channel

    if not channel_summarizer:
        await interaction.followup.send("❌ Channel summarizer not available", ephemeral=True)
        return

    if not AI_AVAILABLE or not ai_assistant:
        await interaction.followup.send("❌ AI not available for this analysis", ephemeral=True)
        return

    # Validate hours
    if hours < 24:
        await interaction.followup.send("❌ Need at least 24 hours of history to judge these muppets!", ephemeral=True)
        return
    if hours > 720:  # 30 days max
        await interaction.followup.send("❌ Max 720 hours (30 days). I ain't reading a novel!", ephemeral=True)
        return

    try:
        # Fetch messages
        messages = await channel_summarizer.fetch_messages(target_channel, hours, limit=1000)

        if not messages or len(messages) < 10:
            await interaction.followup.send(
                f"❌ Not enough chat activity in #{target_channel.name} to analyze! Need more messages to judge you lot."
            )
            return

        # Format messages for analysis
        formatted_messages = channel_summarizer.format_messages_for_summary(messages)

        # Count participation
        participant_counts = {}
        for msg in messages:
            author = msg.author.display_name
            author_id = msg.author.id
            if not msg.author.bot:  # Skip bots
                if author not in participant_counts:
                    participant_counts[author] = {"count": 0, "id": author_id}
                participant_counts[author]["count"] += 1

        # Sort by participation
        sorted_participants = sorted(
            participant_counts.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        # Build participation summary
        participation_summary = "Chat Participation (last {} hours):\n".format(hours)
        for name, data in sorted_participants[:15]:  # Top 15
            participation_summary += f"- {name}: {data['count']} messages\n"

        # Create the AI prompt
        num_participants = len(participant_counts)
        participant_names = ", ".join(participant_counts.keys())

        prompt = f"""You are Harry, a completely insane and hilariously sarcastic CFB 26 league assistant. You've been asked to analyze chat activity and recommend who should be the new co-commissioner.

⚠️ THERE ARE EXACTLY {num_participants} PARTICIPANTS TO RANK: {participant_names}
⚠️ YOUR OUTPUT MUST HAVE EXACTLY {num_participants} RANKINGS (#{1} through #{num_participants})
⚠️ EACH PERSON APPEARS ONLY ONCE - NO DUPLICATES!

PARTICIPATION DATA:
{participation_summary}

RECENT CHAT MESSAGES (sample):
{formatted_messages[:8000]}

YOUR TASK:
Analyze each active participant and rate them on these factors (1-10 scale):

📊 **ANALYSIS FACTORS:**
1. **Activity Level** - How often do they show up and participate?
2. **Helpfulness** - Do they answer questions and help others?
3. **Leadership** - Do they take initiative and organize things?
4. **🚨 Asshole Detector** - Are they a dick? Do they start drama? Toxic behavior?
5. **Reliability** - Do they follow through? Play their games on time?
6. **Humor/Vibes** - Are they fun to have around or a buzzkill?
7. **Knowledge** - Do they know the rules and the game?
8. **Drama Score** - Do they cause unnecessary drama? (Lower is better)

Based on your analysis:
1. Rate EVERY participant with scores and a summary
2. Pick your TOP RECOMMENDATION for co-commissioner
3. Call out the BIGGEST ASSHOLE who should NEVER be commish
4. Roast everyone appropriately

FORMAT YOUR RESPONSE LIKE THIS:

🏆 **HARRY'S CO-COMMISSIONER ANALYSIS**

**📊 FULL RANKINGS (Best to Worst):**

**#1. [Name]** ✅ RECOMMENDED
- 📊 Activity: X/10 | 🤝 Helpful: X/10 | 👑 Leadership: X/10
- 🚨 Asshole: X/10 | 🎭 Drama: X/10 | 😂 Vibes: X/10
- **Overall: X/10** - [2-3 sentence sarcastic roast/commentary about them]

**#2. [Name]**
- 📊 Activity: X/10 | 🤝 Helpful: X/10 | 👑 Leadership: X/10
- 🚨 Asshole: X/10 | 🎭 Drama: X/10 | 😂 Vibes: X/10
- **Overall: X/10** - [2-3 sentence sarcastic roast/commentary]

[Continue for ALL participants, ranked from best to worst]

**#[Last]. [Name]** 🚨 DO NOT PICK
- 📊 Activity: X/10 | 🤝 Helpful: X/10 | 👑 Leadership: X/10
- 🚨 Asshole: X/10 | 🎭 Drama: X/10 | 😂 Vibes: X/10
- **Overall: X/10** - [Brutal but funny roast of why they're last]

---
🏆 **FINAL VERDICT:** [Winner Name] should be co-commish because [brief funny reason]
🚫 **DO NOT PICK:** [Last Ranked Name] - [Why they're a terrible co-commish candidate]
🚨 **BIGGEST ASSHOLE:** [Name with highest asshole score] - [Savage one-liner about why they're the biggest dick]

⚠️⚠️⚠️ CRITICAL RULES - READ CAREFULLY ⚠️⚠️⚠️
1. There are EXACTLY {num_participants} people. You MUST have EXACTLY {num_participants} rankings.
2. Each person appears ONLY ONCE! If you list someone twice, you FAILED.
3. The names are: {participant_names} - rank ALL of them, each ONE time only.
4. #1 is the BEST candidate for co-commissioner, #{num_participants} is the WORST candidate.
5. FINAL VERDICT winner must be #1 ranked person.
6. DO NOT PICK is the #{num_participants} ranked person - they're the worst CO-COMMISH CANDIDATE
   - Could be due to: low activity, unreliable, bad leadership, absent, etc.
7. BIGGEST ASSHOLE is whoever has the HIGHEST "🚨 Asshole" score - this could be ANYONE!
   - Could be #1 ranked (great leader but a dick) or #last (inactive AND a dick) or anyone in between
   - Look at the messages - who starts drama? Who is toxic? Who is rude to others?
   - If everyone has low asshole scores (0-2), say "No major assholes detected... yet 👀"
8. DO NOT PICK and BIGGEST ASSHOLE can be DIFFERENT people or the SAME person

Be extremely sarcastic, funny, and insane. Give each person a proper roast!"""

        # Ask AI with higher token limit for full analysis with proper roasts
        response = await ai_assistant.ask_openai(prompt, "Co-Commissioner Selection Analysis", max_tokens=2000)
        if not response:
            response = await ai_assistant.ask_anthropic(prompt, "Co-Commissioner Selection Analysis", max_tokens=2000)

        if not response:
            await interaction.followup.send("❌ AI couldn't analyze the chat. Maybe you're all equally terrible?")
            return

        # Discord embed description limit is 4096 chars
        # If response is too long, send as regular message(s) instead
        stats_text = (f"\n\n---\n📊 **Analysis Details**\n"
                      f"📍 Channel: **#{target_channel.name}**\n"
                      f"📨 Analyzed **{len(messages)}** messages over **{hours}** hours\n"
                      f"👥 **{len(participant_counts)}** participants evaluated\n"
                      f"🚨 Asshole detector: **ACTIVE**\n"
                      f"*Use /set_co_commish to make it official!*")

        full_response = f"# 👑 Co-Commissioner Selection Analysis\n\n{response}{stats_text}"

        # Discord message limit is 2000 chars - split if needed
        if len(full_response) <= 2000:
            await interaction.followup.send(full_response)
        else:
            # Split into chunks
            chunks = []
            current_chunk = ""

            for line in full_response.split('\n'):
                if len(current_chunk) + len(line) + 1 > 1900:  # Leave some buffer
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += '\n' + line if current_chunk else line

            if current_chunk:
                chunks.append(current_chunk)

            # Send each chunk
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(chunk)
                else:
                    await interaction.channel.send(chunk)
        logger.info(f"👑 Co-commish analysis completed by {interaction.user} for #{target_channel.name}")

    except Exception as e:
        logger.error(f"❌ Error in pick_commish: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Something went wrong analyzing you muppets: {str(e)}")

# ==================== Owner Nagging Commands (Bot Owner Only) ====================

@bot.tree.command(name="nag_owner", description="Start spamming the league owner to advance (Bot Owner only)")
@discord.app_commands.describe(
    interval="How often to nag in minutes (default: 5)"
)
async def nag_owner(interaction: discord.Interaction, interval: int = 5):
    """Start nagging the league owner to advance the week"""
    # This is for the bot owner ONLY - check application info
    try:
        app_info = await bot.application_info()
        bot_owner_id = app_info.owner.id if app_info.owner else None
    except Exception:
        bot_owner_id = None  # Couldn't fetch app info

    if not bot_owner_id or interaction.user.id != bot_owner_id:
        await interaction.response.send_message(
            "❌ Nice try, but only the bot owner can unleash this chaos! 😈",
            ephemeral=True
        )
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    # Check if league owner is set
    staff = timekeeper_manager.get_league_staff()
    if not staff['owner_id']:
        await interaction.response.send_message(
            "❌ No league owner set! Use `/set_league_owner` first, ya numpty!",
            ephemeral=True
        )
        return

    # Validate interval
    if interval < 1:
        await interaction.response.send_message("❌ Interval must be at least 1 minute!", ephemeral=True)
        return
    if interval > 60:
        await interaction.response.send_message("❌ Max interval is 60 minutes. We want to annoy 'em, not forget about 'em!", ephemeral=True)
        return

    # Check if already nagging
    if timekeeper_manager.is_nagging():
        await interaction.response.send_message(
            "❌ Already nagging the owner! Use `/stop_nag` to stop first.",
            ephemeral=True
        )
        return

    success = await timekeeper_manager.start_nagging(interval)

    if success:
        embed = discord.Embed(
            title="😈 NAGGING ACTIVATED!",
            description=f"Alright, let the chaos begin!\n\n"
                       f"**Target:** <@{staff['owner_id']}>\n"
                       f"**Frequency:** Every {interval} minute{'s' if interval > 1 else ''}\n\n"
                       f"They're gonna LOVE this! 🔥\n\n"
                       f"Use `/stop_nag` when they finally advance (or beg for mercy).",
            color=0xff0000
        )
        embed.set_footer(text="Harry's Revenge System 🏈 | May God have mercy on their soul")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"😈 Nagging started by {interaction.user} - interval: {interval} minutes")
    else:
        await interaction.response.send_message("❌ Failed to start nagging!", ephemeral=True)

@bot.tree.command(name="stop_nag", description="Stop spamming the league owner (Bot Owner only)")
async def stop_nag(interaction: discord.Interaction):
    """Stop nagging the league owner"""
    # This is for the bot owner ONLY
    try:
        app_info = await bot.application_info()
        bot_owner_id = app_info.owner.id if app_info.owner else None
    except Exception:
        bot_owner_id = None  # Couldn't fetch app info

    if not bot_owner_id or interaction.user.id != bot_owner_id:
        await interaction.response.send_message(
            "❌ Only the bot owner can stop the chaos they started! 😈",
            ephemeral=True
        )
        return

    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    if not timekeeper_manager.is_nagging():
        await interaction.response.send_message(
            "❌ Not currently nagging anyone. Use `/nag_owner` to start!",
            ephemeral=True
        )
        return

    success = await timekeeper_manager.stop_nagging()

    if success:
        embed = discord.Embed(
            title="😇 Nagging Stopped",
            description="Alright, I'll give 'em a break... for now.\n\n"
                       "The league owner has been spared (temporarily).",
            color=0x00ff00
        )
        embed.set_footer(text="Harry's Mercy System 🏈 | They got lucky this time")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"😇 Nagging stopped by {interaction.user}")
    else:
        await interaction.response.send_message("❌ Failed to stop nagging!", ephemeral=True)

@bot.tree.command(name="summarize", description="Summarize channel activity for a time period")
async def summarize_channel(
    interaction: discord.Interaction,
    hours: int = 24,
    focus: Optional[str] = None
):
    """
    Summarize channel activity

    Args:
        hours: Number of hours to look back (default: 24)
        focus: Optional focus area for the summary (e.g., "rules", "voting", "decisions")
    """
    if not channel_summarizer:
        await interaction.response.send_message("❌ Channel summarizer not available", ephemeral=True)
        return

    try:
        # Send initial response IMMEDIATELY to avoid timeout
        await interaction.response.defer()

        # Validate hours input
        if hours < 1:
            hours = 1
        elif hours > 168:  # Max 1 week
            hours = 168

        # Clean up focus parameter
        focus_text = focus.strip() if focus else None
        if focus_text:
            focus_text = focus_text.strip()

        # Send "working" message
        focus_description = f" focusing on **{focus_text}**" if focus_text else ""
        embed = discord.Embed(
            title="📊 Generating Summary...",
            description=f"Right then, let me 'ave a look through the last **{hours} hours** of messages in this channel{focus_description}...\n\nThis might take a mo', so don't get your knickers in a twist!",
            color=0xffa500
        )
        await interaction.followup.send(embed=embed)

        # Generate the summary
        focus_log = f" (focus: {focus_text})" if focus_text else ""
        logger.info(f"📊 Summary requested by {interaction.user} for #{interaction.channel.name} ({hours} hours{focus_log})")
        summary = await channel_summarizer.get_channel_summary(
            interaction.channel,
            hours=hours,
            focus=focus_text,
            limit=500
        )

        # Format the response
        title_focus = f" - {focus_text.title()}" if focus_text else ""
        embed = discord.Embed(
            title=f"📊 Channel Summary - Last {hours} Hour{'s' if hours > 1 else ''}{title_focus}",
            description=summary,
            color=0x00ff00
        )

        embed.add_field(
            name="📍 Channel",
            value=f"#{interaction.channel.name}",
            inline=True
        )

        embed.add_field(
            name="⏰ Time Period",
            value=f"Last {hours} hour{'s' if hours > 1 else ''}",
            inline=True
        )

        if focus_text:
            embed.add_field(
                name="🎯 Focus",
                value=focus_text,
                inline=True
            )

        embed.set_footer(text=f"Harry's Channel Summary 🏈 | Requested by {interaction.user.display_name}")

        await interaction.followup.send(embed=embed)
        logger.info(f"✅ Summary delivered for #{interaction.channel.name}")

    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="Oi! I don't 'ave permission to read message history in this channel, ya muppet!\n\n**To fix:** Give me 'Read Message History' permission in channel settings.",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"❌ Error generating summary: {e}")
        embed = discord.Embed(
            title="❌ Summary Failed",
            description=f"Bloody hell! Somethin' went wrong while generatin' the summary:\n\n`{str(e)}`\n\nTry again later, mate!",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="add_rule", description="Add a new rule to the charter (Admin only)")
async def add_charter_rule(
    interaction: discord.Interaction,
    section_title: str,
    rule_content: str,
    position: str = "end"
):
    """
    Add a new rule section to the charter

    Args:
        section_title: Title of the new rule section
        rule_content: Content of the rule
        position: Where to add it (default: "end")
    """
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions to edit the charter, ya muppet!", ephemeral=True)
        return

    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    # Send initial response
    await interaction.response.defer()

    try:
        # Format the rule with AI if available
        formatted_content = await charter_editor.format_rule_with_ai(rule_content)

        # Add the rule
        result = await charter_editor.add_rule_section(
            section_title=section_title,
            section_content=formatted_content or rule_content,
            position=position
        )

        if result['success']:
            embed = discord.Embed(
                title="✅ Rule Added Successfully!",
                description=f"Right then! I've added the new rule to the charter, mate!\n\n**Section**: {section_title}\n**Position**: {position}",
                color=0x00ff00
            )
            embed.add_field(
                name="📝 Content",
                value=formatted_content[:1000] if formatted_content else rule_content[:1000],
                inline=False
            )
            embed.set_footer(text=f"Charter edited by {interaction.user.display_name} 🏈")
            await interaction.followup.send(embed=embed)
            logger.info(f"✅ Rule added by {interaction.user}: {section_title}")
        else:
            embed = discord.Embed(
                title="❌ Failed to Add Rule",
                description=f"Bloody hell! Couldn't add the rule:\n\n{result['message']}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"❌ Error adding rule: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Somethin' went wrong, mate:\n\n`{str(e)}`",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="update_rule", description="Update an existing rule in the charter (Admin only)")
async def update_charter_rule(
    interaction: discord.Interaction,
    section_identifier: str,
    new_content: str
):
    """
    Update an existing rule section

    Args:
        section_identifier: Identifier for the section to update (e.g., "1.1", "Scheduling")
        new_content: New content for the section
    """
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions to edit the charter!", ephemeral=True)
        return

    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    # Send initial response
    await interaction.response.defer()

    try:
        # Format the content with AI if available
        formatted_content = await charter_editor.format_rule_with_ai(new_content)

        # Update the rule
        result = await charter_editor.update_rule_section(
            section_identifier=section_identifier,
            new_content=formatted_content or new_content
        )

        if result['success']:
            embed = discord.Embed(
                title="✅ Rule Updated Successfully!",
                description=f"Sorted! I've updated that section for ya, mate!\n\n**Section**: {section_identifier}",
                color=0x00ff00
            )
            embed.add_field(
                name="📝 New Content",
                value=(formatted_content or new_content)[:1000],
                inline=False
            )
            embed.set_footer(text=f"Charter updated by {interaction.user.display_name} 🏈")
            await interaction.followup.send(embed=embed)
            logger.info(f"✅ Rule updated by {interaction.user}: {section_identifier}")
        else:
            embed = discord.Embed(
                title="❌ Failed to Update Rule",
                description=f"Couldn't update the rule, mate:\n\n{result['message']}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"❌ Error updating rule: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Somethin' went wrong:\n\n`{str(e)}`",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="view_charter_backups", description="View available charter backups (Admin only)")
async def view_backups(interaction: discord.Interaction):
    """View available charter backups"""
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions to view backups!", ephemeral=True)
        return

    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    try:
        backups = charter_editor.get_backup_list()

        if not backups:
            embed = discord.Embed(
                title="📋 Charter Backups",
                description="No backups found, mate! The charter hasn't been backed up yet.",
                color=0x808080
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Charter Backups",
            description=f"Found **{len(backups)}** charter backup{'s' if len(backups) > 1 else ''}!",
            color=0x00ff00
        )

        # Show up to 10 most recent backups
        for backup in backups[:10]:
            timestamp = backup['modified'].strftime('%Y-%m-%d %I:%M %p')
            size_kb = backup['size'] / 1024

            embed.add_field(
                name=f"📄 {backup['filename']}",
                value=f"**Date**: {timestamp}\n**Size**: {size_kb:.1f} KB",
                inline=False
            )

        if len(backups) > 10:
            embed.add_field(
                name="ℹ️ Note",
                value=f"Showing 10 most recent backups. Total backups: {len(backups)}",
                inline=False
            )

        embed.set_footer(text="Use /restore_charter_backup to restore a backup")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"❌ Error viewing backups: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Couldn't get the backups list:\n\n`{str(e)}`",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="restore_charter_backup", description="Restore charter from a backup (Admin only)")
async def restore_backup(interaction: discord.Interaction, backup_filename: str):
    """
    Restore the charter from a backup

    Args:
        backup_filename: Name of the backup file to restore
    """
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need administrator permissions to restore backups!", ephemeral=True)
        return

    if not charter_editor:
        await interaction.response.send_message("❌ Charter editor not available", ephemeral=True)
        return

    # Send initial response
    await interaction.response.defer()

    try:
        success = charter_editor.restore_backup(backup_filename)

        if success:
            embed = discord.Embed(
                title="✅ Charter Restored!",
                description=f"Right then! Charter has been restored from backup:\n\n**Backup**: {backup_filename}\n\nThe current charter was backed up before restorin', so don't worry!",
                color=0x00ff00
            )
            embed.set_footer(text=f"Charter restored by {interaction.user.display_name} 🏈")
            await interaction.followup.send(embed=embed)
            logger.info(f"✅ Charter restored by {interaction.user} from {backup_filename}")
        else:
            embed = discord.Embed(
                title="❌ Restore Failed",
                description=f"Couldn't restore the charter from that backup, mate!\n\nMake sure the filename is correct.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"❌ Error restoring backup: {e}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Somethin' went wrong:\n\n`{str(e)}`",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="add_bot_admin", description="Add a user as bot admin (Admin only)")
async def add_bot_admin(interaction: discord.Interaction, user: discord.Member):
    """
    Add a user as bot admin

    Args:
        user: The Discord user to make a bot admin
    """
    if not admin_manager:
        await interaction.response.send_message("❌ Admin manager not available", ephemeral=True)
        return

    # Check if command user is admin (either Discord admin or bot admin)
    if not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to use this command, ya muppet!", ephemeral=True)
        return

    # Add the user as admin
    success = admin_manager.add_admin(user.id)

    if success:
        embed = discord.Embed(
            title="✅ Bot Admin Added!",
            description=f"Right then! **{user.display_name}** is now a bot admin!\n\nThey can now use all admin commands.",
            color=0x00ff00
        )
        embed.set_footer(text=f"Added by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f"✅ Bot admin added: {user.display_name} ({user.id}) by {interaction.user.display_name}")
    else:
        embed = discord.Embed(
            title="ℹ️ Already an Admin",
            description=f"{user.display_name} is already a bot admin, mate!",
            color=0xffa500
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="remove_bot_admin", description="Remove a user as bot admin (Admin only)")
async def remove_bot_admin(interaction: discord.Interaction, user: discord.Member):
    """
    Remove a user as bot admin

    Args:
        user: The Discord user to remove as bot admin
    """
    if not admin_manager:
        await interaction.response.send_message("❌ Admin manager not available", ephemeral=True)
        return

    # Check if command user is admin
    if not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to use this command!", ephemeral=True)
        return

    # Remove the user as admin
    success = admin_manager.remove_admin(user.id)

    if success:
        embed = discord.Embed(
            title="✅ Bot Admin Removed",
            description=f"Right then! **{user.display_name}** is no longer a bot admin.",
            color=0xff0000
        )
        embed.set_footer(text=f"Removed by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f"✅ Bot admin removed: {user.display_name} ({user.id}) by {interaction.user.display_name}")
    else:
        embed = discord.Embed(
            title="ℹ️ Not an Admin",
            description=f"{user.display_name} isn't a bot admin, mate!",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="list_bot_admins", description="List all bot admins")
async def list_bot_admins(interaction: discord.Interaction):
    """List all bot admins"""
    if not admin_manager:
        await interaction.response.send_message("❌ Admin manager not available", ephemeral=True)
        return

    admin_ids = admin_manager.get_admin_list()

    if not admin_ids:
        embed = discord.Embed(
            title="🔐 Bot Admins",
            description="No bot-specific admins configured.\n\nAnyone with Discord Administrator permission can use admin commands.\n\nUse `/add_bot_admin @user` to add bot admins!",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="🔐 Bot Admins",
        description=f"Found **{len(admin_ids)}** bot admin{'s' if len(admin_ids) > 1 else ''}:",
        color=0x00ff00
    )

    # Try to fetch user info for each admin
    admin_info = []
    for admin_id in admin_ids:
        try:
            user = await bot.fetch_user(admin_id)
            admin_info.append(f"• **{user.display_name}** (`{user.name}`) - ID: {admin_id}")
        except (discord.NotFound, discord.HTTPException):
            admin_info.append(f"• User ID: {admin_id} (user not found)")

    embed.add_field(
        name="📋 Admin List",
        value="\n".join(admin_info) if admin_info else "No admins",
        inline=False
    )

    embed.add_field(
        name="ℹ️ Note",
        value="Users with Discord Administrator permission also have bot admin access.",
        inline=False
    )

    embed.set_footer(text="CFB 26 League Bot - Admin Management")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="block_channel", description="Block unprompted responses in a channel (Admin only)")
async def block_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """
    Block unprompted responses in a channel (Harry can still be @mentioned)

    Args:
        channel: The channel to block
    """
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to block channels, ya muppet!", ephemeral=True)
        return

    if not channel_manager:
        await interaction.response.send_message("❌ Channel manager not available", ephemeral=True)
        return

    was_blocked = channel_manager.block_channel(channel.id)

    if was_blocked:
        embed = discord.Embed(
            title="🔇 Channel Blocked!",
            description=f"Right then! I won't make unprompted responses in {channel.mention} anymore.\n\n**But:** You can still @mention me there for questions!\n\nI'll just stay quiet unless you ask, yeah?",
            color=0xff9900
        )
        embed.add_field(
            name="📋 How It Works",
            value="• **@mentions still work** - I'll respond when you ping me\n• **No unprompted replies** - I won't jump into conversations\n• **Slash commands work** - All `/` commands still function",
            inline=False
        )
        embed.set_footer(text=f"Blocked by {interaction.user.display_name} 🔇")
        await interaction.response.send_message(embed=embed)
        logger.info(f"🔇 {interaction.user} blocked channel #{channel.name} (ID: {channel.id})")
    else:
        embed = discord.Embed(
            title="ℹ️ Already Blocked",
            description=f"That channel is already blocked, mate!\n\n{channel.mention} is on the blocked list.",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="unblock_channel", description="Allow unprompted responses in a channel (Admin only)")
async def unblock_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    """
    Allow unprompted responses in a channel

    Args:
        channel: The channel to unblock
    """
    # Check if user is admin
    if not admin_manager or not admin_manager.is_admin(interaction.user, interaction):
        await interaction.response.send_message("❌ You need to be a bot admin to unblock channels, ya muppet!", ephemeral=True)
        return

    if not channel_manager:
        await interaction.response.send_message("❌ Channel manager not available", ephemeral=True)
        return

    was_unblocked = channel_manager.unblock_channel(channel.id)

    if was_unblocked:
        embed = discord.Embed(
            title="🔊 Channel Unblocked!",
            description=f"Brilliant! I can make unprompted responses in {channel.mention} again!\n\nI'll jump in when I see league questions and interesting conversations!",
            color=0x00ff00
        )
        embed.set_footer(text=f"Unblocked by {interaction.user.display_name} 🔊")
        await interaction.response.send_message(embed=embed)
        logger.info(f"🔊 {interaction.user} unblocked channel #{channel.name} (ID: {channel.id})")
    else:
        embed = discord.Embed(
            title="ℹ️ Not Blocked",
            description=f"That channel wasn't blocked, mate!\n\n{channel.mention} already allows unprompted responses.",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="list_blocked_channels", description="Show all blocked channels")
async def list_blocked_channels(interaction: discord.Interaction):
    """Show all channels where unprompted responses are blocked"""
    if not channel_manager:
        await interaction.response.send_message("❌ Channel manager not available", ephemeral=True)
        return

    blocked_ids = channel_manager.get_blocked_channels()

    if not blocked_ids:
        embed = discord.Embed(
            title="🔊 No Blocked Channels",
            description="No channels are blocked!\n\nI can make unprompted responses in all channels.\n\nUse `/block_channel #channel` to block channels (Admin only).",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(
        title="🔇 Blocked Channels",
        description=f"Found **{len(blocked_ids)}** blocked channel{'s' if len(blocked_ids) > 1 else ''}:\n\n**Note:** I can still be @mentioned in these channels!",
        color=0xff9900
    )

    # Try to fetch channel info for each blocked channel
    channel_info = []
    for channel_id in blocked_ids:
        try:
            channel = bot.get_channel(channel_id)
            if channel:
                channel_info.append(f"• {channel.mention} (`#{channel.name}`) - ID: {channel_id}")
            else:
                channel_info.append(f"• Channel ID: {channel_id} (channel not found)")
        except (discord.NotFound, discord.HTTPException):
            channel_info.append(f"• Channel ID: {channel_id} (error fetching info)")

    embed.add_field(
        name="📋 Blocked Channels List",
        value="\n".join(channel_info) if channel_info else "No channels",
        inline=False
    )

    embed.add_field(
        name="ℹ️ How It Works",
        value="• **@mentions still work** - I respond when you ping me\n• **No unprompted replies** - I won't jump into conversations\n• **Admins can manage** - Use `/block_channel` or `/unblock_channel`",
        inline=False
    )

    embed.set_footer(text="CFB 26 League Bot - Channel Management")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="config", description="Configure Harry's features for this server")
@app_commands.describe(
    action="What to do: view, enable, or disable",
    module="Which module: cfb_data or league"
)
@app_commands.choices(action=[
    app_commands.Choice(name="view", value="view"),
    app_commands.Choice(name="enable", value="enable"),
    app_commands.Choice(name="disable", value="disable"),
])
@app_commands.choices(module=[
    app_commands.Choice(name="cfb_data - Player lookup, rankings, matchups, etc.", value="cfb_data"),
    app_commands.Choice(name="league - Timer, charter, rules, dynasty features", value="league"),
])
async def config_command(
    interaction: discord.Interaction,
    action: str = "view",
    module: str = None
):
    """
    Configure which features Harry has enabled on this server.

    Modules:
    - core: Always enabled - Harry's personality, general AI chat
    - cfb_data: Player lookup, rankings, matchups, schedules, draft, transfers
    - league: Timer, advance, charter, rules, league staff, dynasty features
    """
    if not interaction.guild:
        await interaction.response.send_message("❌ This command only works in servers, not DMs!", ephemeral=True)
        return

    guild_id = interaction.guild.id

    # Check admin for enable/disable
    if action in ["enable", "disable"]:
        is_admin = (
            interaction.user.guild_permissions.administrator or
            (admin_manager and admin_manager.is_admin(interaction.user, interaction))
        )
        if not is_admin:
            await interaction.response.send_message(
                "❌ Only server admins can change feature settings, ya muppet!",
                ephemeral=True
            )
            return

    if action == "view":
        # Show current configuration
        enabled = server_config.get_enabled_modules(guild_id)

        embed = discord.Embed(
            title="⚙️ Harry's Configuration",
            description=f"Feature settings for **{interaction.guild.name}**",
            color=0x1e90ff
        )

        for mod in FeatureModule:
            is_enabled = mod.value in enabled
            status = "✅ Enabled" if is_enabled else "❌ Disabled"
            if mod == FeatureModule.CORE:
                status = "✅ Always On"

            desc = server_config.get_module_description(mod)
            commands = server_config.get_module_commands(mod)
            cmd_list = ", ".join([f"`/{c}`" for c in commands[:5]])
            if len(commands) > 5:
                cmd_list += f" +{len(commands) - 5} more"

            embed.add_field(
                name=f"{desc}",
                value=f"**Status:** {status}\n**Commands:** {cmd_list}",
                inline=False
            )

        embed.add_field(
            name="💡 How to Change",
            value="`/config enable cfb_data` - Enable CFB data features\n`/config disable league` - Disable dynasty features",
            inline=False
        )

        embed.set_footer(text="Harry's Server Config 🏈")
        await interaction.response.send_message(embed=embed)

    elif action == "enable":
        if not module:
            await interaction.response.send_message("❌ Please specify a module to enable!", ephemeral=True)
            return

        try:
            mod = FeatureModule(module)
        except ValueError:
            await interaction.response.send_message(f"❌ Unknown module: {module}", ephemeral=True)
            return

        if mod == FeatureModule.CORE:
            await interaction.response.send_message("Core features are always enabled, mate! Can't turn off my personality! 😎", ephemeral=True)
            return

        server_config.enable_module(guild_id, mod)
        await server_config.save_to_discord()

        commands = server_config.get_module_commands(mod)
        cmd_list = ", ".join([f"`/{c}`" for c in commands[:8]])

        embed = discord.Embed(
            title="✅ Module Enabled!",
            description=f"**{mod.value.upper()}** features are now enabled for this server!",
            color=0x00ff00
        )
        embed.add_field(
            name="Available Commands",
            value=cmd_list + (f"\n+{len(commands) - 8} more" if len(commands) > 8 else ""),
            inline=False
        )
        embed.set_footer(text="Harry's Server Config 🏈")
        await interaction.response.send_message(embed=embed)

    elif action == "disable":
        if not module:
            await interaction.response.send_message("❌ Please specify a module to disable!", ephemeral=True)
            return

        try:
            mod = FeatureModule(module)
        except ValueError:
            await interaction.response.send_message(f"❌ Unknown module: {module}", ephemeral=True)
            return

        if mod == FeatureModule.CORE:
            await interaction.response.send_message("Nice try, but you can't turn off my personality! I'm always here, mate! 😏", ephemeral=True)
            return

        server_config.disable_module(guild_id, mod)
        await server_config.save_to_discord()

        embed = discord.Embed(
            title="❌ Module Disabled",
            description=f"**{mod.value.upper()}** features are now disabled for this server.",
            color=0xff6600
        )
        embed.add_field(
            name="Re-enable Anytime",
            value=f"`/config enable {mod.value}` to turn it back on",
            inline=False
        )
        embed.set_footer(text="Harry's Server Config 🏈")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="channel", description="Manage which channels Harry can respond in")
@app_commands.describe(
    action="What to do: view, enable, disable, or toggle_auto",
    channel="Which channel to configure (defaults to current channel)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="view - See channel settings", value="view"),
    app_commands.Choice(name="enable - Allow Harry in this channel", value="enable"),
    app_commands.Choice(name="disable - Remove Harry from this channel", value="disable"),
    app_commands.Choice(name="disable_all - Remove Harry from ALL channels", value="disable_all"),
    app_commands.Choice(name="toggle_auto - Toggle auto-responses for this channel", value="toggle_auto"),
])
async def channel_command(
    interaction: discord.Interaction,
    action: str = "view",
    channel: discord.TextChannel = None
):
    """
    Manage which channels Harry can respond in.
    
    By default, Harry is DISABLED everywhere. You must explicitly enable
    channels for him to respond in using /channel enable.
    """
    if not interaction.guild:
        await interaction.response.send_message("❌ This command only works in servers!", ephemeral=True)
        return

    guild_id = interaction.guild.id
    target_channel = channel or interaction.channel

    # Check admin for enable/disable
    if action in ["enable", "disable", "enable_all", "toggle_auto"]:
        is_admin = (
            interaction.user.guild_permissions.administrator or
            (admin_manager and admin_manager.is_admin(interaction.user, interaction))
        )
        if not is_admin:
            await interaction.response.send_message(
                "❌ Only server admins can change channel settings, ya muppet!",
                ephemeral=True
            )
            return

    if action == "view":
        enabled_channels = server_config.get_enabled_channels(guild_id)
        auto_responses = server_config.auto_responses_enabled(guild_id, target_channel.id)
        channel_enabled = server_config.is_channel_enabled(guild_id, target_channel.id)

        embed = discord.Embed(
            title="📺 Channel Settings",
            description=f"Harry's channel configuration for **{interaction.guild.name}**",
            color=0x1e90ff
        )

        # Current channel status
        current_status = "✅ Enabled" if channel_enabled else "❌ Disabled"
        auto_status = "✅ On" if auto_responses else "❌ Off"
        
        embed.add_field(
            name=f"#{target_channel.name}",
            value=f"**Status:** {current_status}\n**Auto-Responses:** {auto_status}",
            inline=False
        )

        # Show enabled channels
        if enabled_channels:
            channel_mentions = []
            for ch_id in enabled_channels[:10]:
                ch = interaction.guild.get_channel(ch_id)
                if ch:
                    channel_mentions.append(f"#{ch.name}")
            channels_text = ", ".join(channel_mentions)
            if len(enabled_channels) > 10:
                channels_text += f" +{len(enabled_channels) - 10} more"
            embed.add_field(
                name="📋 Enabled Channels",
                value=f"Harry responds in:\n{channels_text}",
                inline=False
            )
        else:
            embed.add_field(
                name="🔇 No Channels Enabled",
                value="Harry is **disabled everywhere**.\nUse `/channel enable` to enable him in specific channels.",
                inline=False
            )

        embed.add_field(
            name="💡 Commands",
            value=(
                "`/channel enable` - Enable Harry in this channel\n"
                "`/channel disable` - Disable Harry in this channel\n"
                "`/channel disable_all` - Disable Harry everywhere\n"
                "`/channel toggle_auto` - Toggle auto-responses here"
            ),
            inline=False
        )

        embed.set_footer(text="Harry's Channel Config 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif action == "enable":
        server_config.enable_channel(guild_id, target_channel.id)
        await server_config.save_to_discord()

        enabled_channels = server_config.get_enabled_channels(guild_id)

        embed = discord.Embed(
            title="✅ Channel Enabled",
            description=f"Harry can now respond in **#{target_channel.name}**!",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📋 Enabled Channels",
            value=f"Harry is now active in **{len(enabled_channels)}** channel(s).",
            inline=False
        )
        
        embed.set_footer(text="Harry's Channel Config 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif action == "disable":
        server_config.disable_channel(guild_id, target_channel.id)
        await server_config.save_to_discord()

        enabled_channels = server_config.get_enabled_channels(guild_id)
        
        embed = discord.Embed(
            title="❌ Channel Disabled",
            description=f"Harry will no longer respond in **#{target_channel.name}**.",
            color=0xff6600
        )
        
        if enabled_channels:
            embed.add_field(
                name="📋 Remaining Channels",
                value=f"Harry is still active in **{len(enabled_channels)}** channel(s).",
                inline=False
            )
        else:
            embed.add_field(
                name="🔇 Harry Disabled",
                value="No channels enabled - Harry is now disabled everywhere.",
                inline=False
            )
        
        embed.set_footer(text="Harry's Channel Config 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif action == "disable_all":
        # Clear the enabled channels list (disables Harry everywhere)
        config = server_config.get_config(guild_id)
        config["enabled_channels"] = []
        await server_config.save_to_discord()

        embed = discord.Embed(
            title="🔇 Harry Disabled Everywhere",
            description="Harry is now **disabled in all channels**.",
            color=0xff6600
        )
        embed.add_field(
            name="💡 To Enable Again",
            value="Use `/channel enable` in the channels where you want Harry to respond.",
            inline=False
        )
        embed.set_footer(text="Harry's Channel Config 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif action == "toggle_auto":
        current = server_config.auto_responses_enabled(guild_id, target_channel.id)
        new_value = not current
        server_config.set_channel_override(guild_id, target_channel.id, "auto_responses", new_value)
        await server_config.save_to_discord()

        status = "✅ Enabled" if new_value else "❌ Disabled"
        embed = discord.Embed(
            title="💬 Auto-Responses Toggled",
            description=f"Auto-responses in **#{target_channel.name}**: {status}",
            color=0x00ff00 if new_value else 0xff6600
        )
        
        if new_value:
            embed.add_field(
                name="What This Means",
                value="Harry will jump in with team banter (like 'Fuck Oregon!') when keywords are mentioned.",
                inline=False
            )
        else:
            embed.add_field(
                name="What This Means",
                value="Harry won't auto-respond to keywords. He'll only respond when @mentioned or asked directly.",
                inline=False
            )
        
        embed.set_footer(text="Harry's Channel Config 🏈")
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="whats_new", description="See what's new with Harry!")
async def whats_new(interaction: discord.Interaction):
    """Show the latest features and updates"""
    embed = discord.Embed(
        title="🎉 What's New with Harry! 🎉",
        description="Oi! Look at all the brilliant new stuff I can do now, mate!",
        color=0x00ff00
    )

    # Feature 1: Advance Timer
    embed.add_field(
        name="⏰ **Advance Timer with Custom Duration** (NEW!)",
        value=(
            "I can now manage advance countdowns with **custom durations**!\n"
            "• `/advance` - Default 48 hour countdown\n"
            "• `/advance 24` - 24 hour countdown\n"
            "• `/advance 72` - 3 day countdown\n"
            "• Automatic reminders at 24h, 12h, 6h, 1h\n"
            "• \"TIME'S UP! LET'S ADVANCE!\" when done\n"
            "• `/time_status` - Check progress with fancy progress bar!"
        ),
        inline=False
    )

    # Feature 2: Channel Summarization
    embed.add_field(
        name="📊 **Channel Summarization** (NEW!)",
        value=(
            "I can read through channel messages and give you AI-powered summaries!\n"
            "• `/summarize` - Last 24 hours\n"
            "• `/summarize 48` - Last 48 hours\n"
            "• `/summarize 24 recruiting` - Focused summary\n"
            "• Shows main topics, decisions, key participants, and notable moments\n"
            "• Perfect for catching up on what you missed!"
        ),
        inline=False
    )

    # Feature 3: Charter Management
    embed.add_field(
        name="📝 **Charter Management** (NEW! - Admin Only)",
        value=(
            "I can edit the league charter directly from Discord!\n"
            "• `/add_rule` - Add new rules to charter\n"
            "• `/update_rule` - Update existing rules\n"
            "• `/view_charter_backups` - See all backups\n"
            "• `/restore_charter_backup` - Restore from backup\n"
            "• Automatic backups before every change\n"
            "• AI-assisted rule formatting!"
        ),
        inline=False
    )

    # Feature 4: Bot Admin System
    embed.add_field(
        name="🔐 **Bot Admin System** (NEW!)",
        value=(
            "Manage bot admins directly through Discord!\n"
            "• `/add_bot_admin @user` - Make someone a bot admin\n"
            "• `/remove_bot_admin @user` - Remove bot admin\n"
            "• `/list_bot_admins` - See all bot admins\n"
            "• Bot admins can use all admin commands\n"
            "• Discord Administrators also have bot admin access"
        ),
        inline=False
    )

    # Other improvements
    embed.add_field(
        name="✨ **Other Improvements**",
        value=(
            "• Better error handling\n"
            "• Improved logging\n"
            "• More sarcastic responses (you're welcome!)\n"
            "• All features maintain my cockney personality!"
        ),
        inline=False
    )

    embed.add_field(
        name="📖 **Learn More**",
        value="Use `/help_cfb` to see all available commands!",
        inline=False
    )

    # Add version info
    if version_manager:
        current_ver = version_manager.get_current_version()
        embed.set_footer(text=f"Harry v{current_ver} - Your CFB 26 League Assistant 🏈 | Updated November 2025")
    else:
        embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈 | Updated November 2025")

    embed.set_thumbnail(url="https://i.imgur.com/3xzKq7L.png")  # Football emoji as thumbnail

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="version", description="Show current bot version")
async def show_version(interaction: discord.Interaction):
    """Show the current version"""
    if not version_manager:
        await interaction.response.send_message("❌ Version manager not available", ephemeral=True)
        return

    current_ver = version_manager.get_current_version()
    version_info = version_manager.get_latest_version_info()

    embed = discord.Embed(
        title=f"🏈 Harry v{current_ver}",
        description=f"{version_info.get('emoji', '🎉')} {version_info.get('title', 'Current Version')}",
        color=0x00ff00
    )

    embed.add_field(
        name="📅 Release Date",
        value=version_info.get('date', 'Unknown'),
        inline=True
    )

    embed.add_field(
        name="📊 Total Versions",
        value=str(len(version_manager.get_all_versions())),
        inline=True
    )

    embed.add_field(
        name="📖 View Details",
        value="Use `/changelog` to see all changes!",
        inline=False
    )

    embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="changelog", description="View version changelog")
async def view_changelog(interaction: discord.Interaction, version: str = None):
    """
    View the changelog for a specific version or all versions

    Args:
        version: Specific version to view (e.g., "1.1.0") or leave blank for summary
    """
    if not version_manager:
        await interaction.response.send_message("❌ Version manager not available", ephemeral=True)
        return

    # If no version specified, show summary of all versions
    if not version:
        embed = discord.Embed(
            title="📜 Harry's Version History",
            description="Here's all the brilliant updates I've had, mate!",
            color=0x00ff00
        )

        summary = version_manager.get_version_summary()
        embed.add_field(
            name="📋 All Versions",
            value=summary,
            inline=False
        )

        embed.add_field(
            name="🔍 View Specific Version",
            value="Use `/changelog 1.1.0` to see details for a specific version!",
            inline=False
        )

        current_ver = version_manager.get_current_version()
        embed.set_footer(text=f"Current Version: v{current_ver}")

        await interaction.response.send_message(embed=embed)
        return

    # Show specific version details
    embed_data = version_manager.format_version_embed_data(version)

    if not embed_data:
        embed = discord.Embed(
            title="❌ Version Not Found",
            description=f"Sorry mate, I don't have any info about version {version}!\n\nUse `/changelog` to see all available versions.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Create embed with version details
    embed = discord.Embed(
        title=embed_data['title'],
        description=embed_data['description'],
        color=0x00ff00
    )

    for field in embed_data['fields']:
        embed.add_field(
            name=field['name'],
            value=field['value'],
            inline=field['inline']
        )

    current_ver = version_manager.get_current_version()
    is_current = version == current_ver
    footer_text = f"Version v{version}" + (" (Current)" if is_current else "")
    embed.set_footer(text=footer_text)

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Use `/help_cfb` for command usage.")
    else:
        print(f"Error: {error}")

def main():
    """Main function to run the bot"""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("❌ DISCORD_BOT_TOKEN not found in environment variables")
        logger.error("📝 Please create a .env file with your bot token")
        exit(1)

    logger.info("🚀 Starting CFB Rules Bot...")
    logger.info(f"📊 Environment: {'Production' if os.getenv('RENDER') else 'Development'}")
    logger.info(f"🤖 AI Available: {AI_AVAILABLE}")
    logger.info(f"📄 Google Docs Available: {GOOGLE_DOCS_AVAILABLE}")

    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        raise

if __name__ == "__main__":
    main()
