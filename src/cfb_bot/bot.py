#!/usr/bin/env python3
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

# Fix for Python 3.13 audioop compatibility
from .utils import audioop_fix

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import json
import asyncio
import logging
import sys
import re
from datetime import datetime, timedelta

# Import timekeeper, summarizer, charter editor, admin manager, version manager, and channel manager
from .utils.timekeeper import TimekeeperManager
from .utils.summarizer import ChannelSummarizer
from .utils.charter_editor import CharterEditor
from .utils.admin_check import AdminManager
from .utils.version_manager import VersionManager
from .utils.channel_manager import ChannelManager

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

# Simple rate limiting to prevent duplicate responses
last_message_time = {}
processed_messages = set()  # Track processed message IDs
processed_content = set()  # Track processed content+author combinations
recent_content_times = {}  # Track content + timestamp for time-based deduplication

@bot.event
async def on_ready():
    """
    Called when the bot is ready and connected to Discord.

    Performs initial setup including:
    - Loading league data
    - Syncing slash commands
    - Logging connection status
    """
    global timekeeper_manager, channel_summarizer, charter_editor, admin_manager, version_manager, channel_manager

    # Initialize version manager first to get version
    version_manager = VersionManager()
    current_version = version_manager.get_current_version()

    logger.info(f'🏈 CFB 26 League Bot ({bot.user}) v{current_version} has connected to Discord!')
    logger.info(f'🔗 Bot ID: {bot.user.id}')
    logger.info(f'📛 Bot Username: {bot.user.name}')
    logger.info(f'🏷️ Bot Display Name: {bot.user.display_name}')
    logger.info(f'📊 Connected to {len(bot.guilds)} guilds')
    logger.info(f'👋 Harry is ready to help with league questions!')

    # Initialize channel manager
    channel_manager = ChannelManager()
    logger.info(f'🔇 Channel manager initialized ({channel_manager.get_blocked_count()} blocked channels)')

    # Initialize admin manager
    admin_manager = AdminManager()
    logger.info(f'🔐 Admin manager initialized ({admin_manager.get_admin_count()} admin(s) configured)')

    # Initialize timekeeper manager
    timekeeper_manager = TimekeeperManager(bot)
    logger.info('⏰ Timekeeper manager initialized')

    # Restore any saved timer state
    await timekeeper_manager.load_saved_state()

    # Initialize channel summarizer (with AI if available)
    channel_summarizer = ChannelSummarizer(ai_assistant if AI_AVAILABLE else None)
    logger.info('📊 Channel summarizer initialized')

    # Initialize charter editor (with AI if available)
    charter_editor = CharterEditor(ai_assistant if AI_AVAILABLE else None)
    logger.info('📝 Charter editor initialized')

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
    # Prevent duplicate processing of the same message (check first!)
    # Check both message ID and content key before processing
    global recent_content_times
    content_key = f"{message.author.id}:{message.content}:{message.channel.id}"
    current_time = asyncio.get_event_loop().time()

    if message.id in processed_messages:
        logger.info(f"⏭️ Skipping duplicate message ID: {message.id}")
        return

    if content_key in processed_content:
        logger.info(f"⏭️ Skipping duplicate content: {content_key[:50]}...")
        return

    # Time-based deduplication: check if same content was processed in last 2 seconds
    if content_key in recent_content_times:
        time_diff = current_time - recent_content_times[content_key]
        if time_diff < 2.0:  # Within 2 seconds
            logger.info(f"⏭️ Skipping duplicate content (time-based): {content_key[:50]}... (seen {time_diff:.2f}s ago)")
            return

    # Add to all tracking sets atomically (before processing)
    processed_messages.add(message.id)
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

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the bot is @mentioned (only responds to @CFB Bot, not just "harry" in text)
    bot_mentioned = False
    if message.mentions:
        for mention in message.mentions:
            if mention.id == bot.user.id:
                bot_mentioned = True
                break

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

    # Check for rivalry/fun responses
    rivalry_keywords = {
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
        'rules': 'Here are the CFB 26 league rules! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
        'league rules': 'Here are the CFB 26 league rules! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
        'charter': 'Here\'s the official CFB 26 league charter! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
        'league charter': 'Here\'s the official CFB 26 league charter! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)'
    }

    rivalry_response = None
    for keyword, response in rivalry_keywords.items():
        if keyword in message.content.lower():
            rivalry_response = response
            break

    # Don't trigger rivalry response if it's a clear question (especially with "harry" mentioned)
    if rivalry_response and (is_question or (bot_mentioned and len(message.content.split()) > 2)):
        rivalry_response = None
        logger.info(f"🔍 Rivalry response overridden: question detected or harry mentioned with context")

    logger.info(f"🔍 Response triggers: is_greeting={is_greeting}, rivalry_response={rivalry_response is not None}")

    # PRIORITY 1: Handle rivalry responses immediately (no AI processing needed)
    if rivalry_response:
        logger.info(f"🏆 Rivalry response triggered: {rivalry_response[:50]}...")
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
        embed.description = rivalry_response
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

                    if is_league_related:
                        # Step 1: Try AI with charter content for league questions
                        charter_question = f"""You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You have a deep, unhinged hatred of the Oregon Ducks. Answer this question using ONLY the league charter content:

Question: {question}

If the charter contains relevant information, provide a helpful answer. If not, respond with "NO_CHARTER_INFO"."""

                        # Log the question and who asked it
                        logger.info(f"🤖 League AI Question from {message.author} ({message.author.id}): {question}")
                        logger.info(f"📝 Full AI prompt: {charter_question[:200]}...")

                        ai_response = await ai_assistant.ask_ai(charter_question, f"{message.author} ({message.author.id})")

                        # Step 2: If no charter info, try general AI search
                        if ai_response and "NO_CHARTER_INFO" in ai_response:
                            logger.info("No charter info found, trying general AI search")
                            general_question = f"""You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You have a deep, unhinged hatred of the Oregon Ducks. Answer this question about CFB 26 league rules, recruiting, transfers, or dynasty management:

Question: {question}

IMPORTANT: Only provide a direct answer if you're confident about CFB 26 league specifics. If you're not sure about the exact league rules, say "I don't have that specific information about our league rules, but you can check our full charter for the official details."

Keep responses concise and helpful. Do NOT mention "charter" unless you truly don't know the answer."""

                            # Log the general AI question
                            logger.info(f"🤖 General AI Question from {message.author} ({message.author.id}): {question}")
                            logger.info(f"📝 General AI prompt: {general_question[:200]}...")

                            ai_response = await ai_assistant.ask_ai(general_question, f"{message.author} ({message.author.id})")
                    else:
                        # For non-league questions, use general AI search directly
                        general_question = f"""You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You have a deep, unhinged hatred of the Oregon Ducks. Answer this question helpfully and accurately:

Question: {question}

Please provide a helpful, accurate answer with maximum sarcasm and wit."""

                        # Log the general AI question
                        logger.info(f"🤖 General AI Question from {message.author} ({message.author.id}): {question}")
                        logger.info(f"📝 General AI prompt: {general_question[:200]}...")

                        ai_response = await ai_assistant.ask_ai(general_question, f"{message.author} ({message.author.id})")
                else:
                    # For non-allowed channels, this should only happen with slash commands
                    # Use general AI without league context
                    general_question = f"""You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You have a deep, unhinged hatred of the Oregon Ducks. Answer this question helpfully and accurately:

Question: {question}

Please provide a helpful, accurate answer with maximum sarcasm and wit. This is a general conversation, not about league rules."""

                    logger.info(f"🤖 General AI Question from {message.author} ({message.author.id}): {question}")
                    logger.info(f"📝 General AI prompt: {general_question[:200]}...")

                    ai_response = await ai_assistant.ask_ai(general_question, f"{message.author} ({message.author.id})")

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

@bot.event
async def on_reaction_add(reaction, user):
    """Handle emoji reactions"""
    # Ignore reactions from the bot itself
    if user == bot.user:
        return

    # Only respond to reactions on Harry's messages
    if reaction.message.author != bot.user:
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
        # Duck emoji - Oregon rivalry
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

@bot.tree.command(name="help_cfb", description="Show all available commands")
async def help_cfb(interaction: discord.Interaction):
    """Show help information"""
    embed = discord.Embed(
        title="🏈 CFB 26 League Bot Commands",
        description="Oi! Here's what I can do for ya, mate!",
        color=0x1e90ff
    )

    # League Rules Commands
    embed.add_field(
        name="📋 **League Rules Commands**",
        value=(
            "• `/rule <rule_name>` - Look up specific league rules\n"
            "• `/recruiting <topic>` - Get recruiting rules\n"
            "• `/dynasty <topic>` - Dynasty management rules\n"
            "• `/charter` - Link to official charter\n"
            "• `/search <term>` - Search the charter"
        ),
        inline=False
    )

    # AI Commands
    embed.add_field(
        name="🤖 **AI Assistant Commands**",
        value=(
            "• `/harry <question>` - Ask me anything!\n"
            "• `/ask <question>` - AI-powered rule answers"
        ),
        inline=False
    )

    # NEW: Timekeeper Commands
    embed.add_field(
        name="⏰ **Advance Timer Commands**",
        value=(
            "• `/advance [hours]` - Start countdown **(Admin only)**\n"
            "  Example: `/advance` = 48 hours\n"
            "  Example: `/advance 24` = 24 hours\n"
            "• `/time_status` - Check countdown progress\n"
            "• `/stop_countdown` - Stop timer **(Admin only)**"
        ),
        inline=False
    )

    # NEW: Summarization Commands
    embed.add_field(
        name="📊 **Channel Summarization**",
        value=(
            "• `/summarize [hours] [focus]` - Summarize channel activity\n"
            "  Example: `/summarize 24` - Last 24 hours\n"
            "  Example: `/summarize 48 recruiting` - Last 48h, focus on recruiting"
        ),
        inline=False
    )

    # NEW: Charter Editing Commands
    embed.add_field(
        name="📝 **Charter Management (Admin Only)**",
        value=(
            "• `/add_rule <title> <content>` - Add new rule\n"
            "• `/update_rule <section> <content>` - Update rule\n"
            "• `/view_charter_backups` - View backups\n"
            "• `/restore_charter_backup <file>` - Restore backup"
        ),
        inline=False
    )

    # Other Commands
    embed.add_field(
        name="🛠️ **Other Commands**",
        value=(
            "• `/team <team_name>` - Team information\n"
            "• `/tokens` - AI usage statistics\n"
            "• `/whats_new` - See latest features!\n"
            "• `/version` - Current bot version\n"
            "• `/changelog [version]` - View version history\n"
            "• `/help_cfb` - Show this message"
        ),
        inline=False
    )

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

            # Make the AI response more conversational
            conversational_question = f"You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You have a deep, unhinged hatred of the Oregon Ducks. Answer this question about CFB 26 league rules in a hilariously sarcastic way: {question}"
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

@bot.tree.command(name="ask", description="Ask Harry anything - league rules or general questions")
async def ask_ai(interaction: discord.Interaction, question: str):
    """Ask AI about league rules or general questions"""
    embed = discord.Embed(
        title="🤖 AI Assistant Response",
        color=0x9b59b6
    )

    if AI_AVAILABLE and ai_assistant:
        try:
            # Send initial response immediately
            await interaction.response.send_message("🤖 Thinking...", ephemeral=True)

            # Log the slash command usage
            guild_name = interaction.guild.name if interaction.guild else "DM"
            logger.info(f"🎯 SLASH COMMAND: /ask from {interaction.user} ({interaction.user.id}) in {guild_name} - '{question}'")
            logger.info(f"🔍 Slash command question: '{question}'")
            logger.info(f"🏠 Server: {guild_name} (ID: {interaction.guild.id if interaction.guild else 'DM'})")

            # Classification for slash commands
            is_question, league_related, matched_keywords = classify_question(question)

            logger.info(f"🔍 CLASSIFICATION: is_question={is_question}, league_related={league_related}")
            if league_related:
                logger.info(f"🎯 Matched keywords: {matched_keywords}")

            # Add Harry's personality to the ask command
            harry_question = f"You are Harry, a friendly but completely insane CFB 26 league assistant. You are extremely sarcastic, witty, and have a dark sense of humor. You have a deep, unhinged hatred of the Oregon Ducks. Answer this question with maximum sarcasm: {question}"

            # For league-related questions, use charter context
            # For general questions, use general AI without charter context
            if league_related:
                # Use charter context for league questions
                response = await ai_assistant.ask_ai(harry_question, f"{interaction.user} ({interaction.user.id})")
                if response:
                    embed.description = response
                    embed.add_field(
                        name="💡 Tip",
                        value="AI responses are based on the league charter. Always verify important rules in the full document.",
                        inline=False
                    )
                else:
                    embed.description = "Sorry, I couldn't get an AI response right now. Please check the charter directly."
            else:
                # For general questions, use AI without charter context
                logger.info("🌍 General question detected - using AI without charter context")
                general_context = "You are Harry, a helpful assistant. Answer general questions helpfully and accurately with your signature sarcasm and wit."

                # Call OpenAI directly with general context
                response = await ai_assistant.ask_openai(harry_question, general_context)
                if not response:
                    # Fallback to Anthropic
                    response = await ai_assistant.ask_anthropic(harry_question, general_context)

                if response:
                    embed.description = response
                    embed.add_field(
                        name="💡 Note",
                        value="This is a general question. For league-specific questions, try `/harry` or `/ask` with league keywords!",
                        inline=False
                    )
                else:
                    embed.description = "Sorry, I couldn't get an AI response right now. Try again later!"
        except Exception as e:
            embed.description = f"Error getting AI response: {str(e)}"
    else:
        embed.description = "AI integration not available. Please check the charter directly or use other commands."

    embed.add_field(
        name="📖 Full Charter",
        value="[Open League Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )

    embed.set_footer(text="CFB 26 League Bot - AI Assistant")

    # Send the actual response
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="advance", description="Start advance countdown timer (Admin only)")
async def start_advance(interaction: discord.Interaction, hours: int = 48):
    """
    Start the advance countdown timer

    Args:
        hours: Number of hours for the countdown (default: 48)
    """
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

    # Start the countdown
    success = timekeeper_manager.start_timer(interaction.channel, hours)

    if success:
        embed = discord.Embed(
            title="⏰ Advance Countdown Started!",
            description=f"Right then, listen up ya wankers!\n\n🏈 **{hours} HOUR COUNTDOWN STARTED** 🏈\n\nYou got **{hours} hours** to get your bleedin' games done!\n\nI'll be remindin' you lot at:\n• 24 hours remaining (if applicable)\n• 12 hours remaining (if applicable)\n• 6 hours remaining (if applicable)\n• 1 hour remaining\n\nAnd when time's up... well, you'll know! 😈",
            color=0x00ff00
        )
        status = timekeeper_manager.get_status(interaction.channel)
        embed.add_field(
            name="⏳ Deadline",
            value=f"{status['end_time'].strftime('%A, %B %d at %I:%M %p')}",
            inline=False
        )
        embed.set_footer(text="Harry's Advance Timer 🏈 | Use /time_status to check progress")
        await interaction.response.send_message(embed=embed)
        logger.info(f"⏰ Advance countdown started by {interaction.user} in {interaction.channel} - {hours} hours")
    else:
        embed = discord.Embed(
            title="❌ Countdown Already Active!",
            description="Oi! There's already a countdown runnin', ya muppet!\n\nUse `/time_status` to check how much time is left.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="time_status", description="Check the current advance countdown status")
async def check_time_status(interaction: discord.Interaction):
    """Check the current advance countdown status"""
    if not timekeeper_manager:
        await interaction.response.send_message("❌ Timekeeper not available", ephemeral=True)
        return

    status = timekeeper_manager.get_status(interaction.channel)

    if not status['active']:
        embed = discord.Embed(
            title="⏰ No Countdown Active",
            description="There ain't no countdown runnin' right now, mate.\n\nUse `/advance` to start the 48-hour countdown.",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed)
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

        embed = discord.Embed(
            title="⏰ Advance Countdown Status",
            description=f"**Time Remaining:** {hours}h {minutes}m\n\n{urgency}",
            color=color
        )

        embed.add_field(
            name="📅 Started",
            value=status['start_time'].strftime('%I:%M %p on %B %d'),
            inline=True
        )
        embed.add_field(
            name="⏳ Deadline",
            value=status['end_time'].strftime('%I:%M %p on %B %d'),
            inline=True
        )

        # Add progress bar
        timer = timekeeper_manager.get_timer(interaction.channel)
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

        embed.set_footer(text="Harry's Advance Timer 🏈")
        await interaction.response.send_message(embed=embed)

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

    success = timekeeper_manager.stop_timer(interaction.channel)

    if success:
        embed = discord.Embed(
            title="⏹️ Countdown Stopped",
            description="Right, countdown's been cancelled then!\n\nAll timers have been stopped.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f"⏹️ Countdown stopped by {interaction.user} in {interaction.channel}")
    else:
        embed = discord.Embed(
            title="❌ No Active Countdown",
            description="There ain't no countdown to stop, ya numpty!",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="summarize", description="Summarize channel activity for a time period")
async def summarize_channel(
    interaction: discord.Interaction,
    hours: int = 24,
    focus: str = None
):
    """
    Summarize channel activity

    Args:
        hours: Number of hours to look back (default: 24)
        focus: Optional focus area for the summary
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

        # Send "working" message
        embed = discord.Embed(
            title="📊 Generating Summary...",
            description=f"Right then, let me 'ave a look through the last **{hours} hours** of messages in this channel...\n\nThis might take a mo', so don't get your knickers in a twist!",
            color=0xffa500
        )
        await interaction.followup.send(embed=embed)

        # Generate the summary
        logger.info(f"📊 Summary requested by {interaction.user} for #{interaction.channel.name} ({hours} hours)")
        summary = await channel_summarizer.get_channel_summary(
            interaction.channel,
            hours=hours,
            focus=focus,
            limit=500
        )

        # Format the response
        embed = discord.Embed(
            title=f"📊 Channel Summary - Last {hours} Hour{'s' if hours > 1 else ''}",
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

        if focus:
            embed.add_field(
                name="🎯 Focus",
                value=focus,
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
        except:
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
        except:
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
