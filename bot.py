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
import audioop_fix

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import json
import asyncio
import logging
import sys
from datetime import datetime

# Optional Google Docs integration
try:
    from google_docs_integration import GoogleDocsIntegration
    GOOGLE_DOCS_AVAILABLE = True
except ImportError:
    GOOGLE_DOCS_AVAILABLE = False

# Optional AI integration
try:
    from ai_integration import AICharterAssistant
    # Check if at least one AI API key is available
    AI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
except ImportError:
    AI_AVAILABLE = False

# Load environment variables
load_dotenv()

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

# Simple rate limiting to prevent duplicate responses
last_message_time = {}
processed_messages = set()  # Track processed message IDs

@bot.event
async def on_ready():
    """
    Called when the bot is ready and connected to Discord.
    
    Performs initial setup including:
    - Loading league data
    - Syncing slash commands
    - Logging connection status
    """
    logger.info(f'🏈 CFB 26 League Bot ({bot.user}) has connected to Discord!')
    logger.info(f'📊 Connected to {len(bot.guilds)} guilds')
    logger.info(f'👋 Harry is ready to help with league questions!')
    
    # Load league data
    await load_league_data()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'✅ Synced {len(synced)} command(s)')
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
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Only respond in #general channel on specific server
    TARGET_SERVER_ID = 1261662233109205144
    TARGET_CHANNEL_NAME = "general"
    
    # Check if we're in the right server and channel
    if not message.guild or message.guild.id != TARGET_SERVER_ID:
        return
    
    if message.channel.name != TARGET_CHANNEL_NAME:
        return
    
    # Comprehensive logging
    guild_name = message.guild.name if message.guild else "DM"
    logger.info(f"📨 Message received: '{message.content}' from {message.author} in #{message.channel} (Server: {guild_name})")
    logger.info(f"📊 Message details: length={len(message.content)}, type={type(message.content)}, repr={repr(message.content)}")
    
    # Skip empty messages
    if not message.content or message.content.strip() == '':
        logger.info(f"⏭️ Skipping empty message from {message.author}")
        return
    
    # Prevent duplicate processing of the same message
    if message.id in processed_messages:
        logger.info(f"⏭️ Duplicate message detected: skipping message {message.id} from {message.author}")
        return
    processed_messages.add(message.id)
    
    # Simple rate limiting to prevent duplicate responses (5 second cooldown per user)
    current_time = asyncio.get_event_loop().time()
    user_id = message.author.id
    if user_id in last_message_time and current_time - last_message_time[user_id] < 5:
        logger.info(f"⏭️ Rate limiting: skipping message from {message.author} (too recent)")
        return
    last_message_time[user_id] = current_time
    
    # Check if the bot is specifically mentioned (not @everyone)
    bot_mentioned = False
    if message.mentions:
        for mention in message.mentions:
            if mention.id == bot.user.id:
                bot_mentioned = True
                break
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
    
    # Check for greetings
    greetings = ['hi harry', 'hello harry', 'hey harry', 'harry', 'hi bot', 'hello bot']
    is_greeting = any(greeting in message.content.lower() for greeting in greetings)
    
    # Check for rivalry/fun responses
    rivalry_keywords = {
        'oregon': 'Fuck Oregon! 🦆💩',
        'ducks': 'Ducks are assholes! 🦆💩',
        'oregon ducks': 'Fuck Oregon! 🦆💩',
        'oregon state': 'Fuck Oregon! 🦆💩',
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
        'georgia': 'Go Dawgs! 🐕',
        'bulldogs': 'Go Dawgs! 🐕',
        'ohio state': 'Go Buckeyes! 🌰',
        'buckeyes': 'Go Buckeyes! 🌰',
        'michigan': 'Go Blue! 💙',
        'wolverines': 'Go Blue! 💙',
        'cfb 26': 'CFB 26 is the best dynasty league! 🏈👑',
        'dynasty': 'Dynasty leagues are the best! 🏆',
        'sim': 'Simming games? Make sure you follow the league rules! 📋',
        'recruit': 'Recruiting is key to dynasty success! 🎯',
        'transfer': 'Transfers can make or break your season! 🔄',
        'penalty': 'Better follow the rules or you\'ll get penalized! ⚠️',
        'harry': 'That\'s me! Harry, your CFB 26 league assistant! 🏈',
        'bot': 'I\'m not just a bot, I\'m Harry! 🏈',
        'ai': 'I\'m powered by AI to help with your league questions! 🤖',
        'help': 'I\'m here to help! Ask me about league rules, recruiting, transfers, or anything else! 💡',
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
    
    # PRIORITY 2: Handle direct mentions with league-related content OR league-related questions
    league_related_question = is_question and any(keyword in message.content.lower() for keyword in ['rule', 'rules', 'charter', 'league', 'recruiting', 'transfer', 'dynasty', 'cfb'])
    league_related_mention = bot_mentioned and any(keyword in message.content.lower() for keyword in ['rule', 'rules', 'charter', 'league', 'recruiting', 'transfer', 'dynasty', 'cfb', 'advance', 'game', 'team', 'player', 'coach', 'schedule', 'playoff', 'bowl', 'conference'])
    
    if league_related_mention or league_related_question:
        logger.info(f"💬 Regular response triggered: bot_mentioned={bot_mentioned}, league_question={league_related_question}")
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
        # Step 1: Try AI with charter content first
        ai_response = None
        if AI_AVAILABLE and ai_assistant:
            try:
                question = message.content
                if bot_mentioned:
                    # Remove the mention from the question
                    question = question.replace(f'<@{bot.user.id}>', '').strip()
                
                # Step 1: Try AI with charter content
                charter_question = f"""You are Harry, a friendly CFB 26 league assistant. Answer this question using ONLY the league charter content:

Question: {question}

If the charter contains relevant information, provide a helpful answer. If not, respond with "NO_CHARTER_INFO"."""

                # Log the question and who asked it
                logger.info(f"🤖 AI Question from {message.author} ({message.author.id}): {question}")
                logger.info(f"📝 Full AI prompt: {charter_question[:200]}...")

                ai_response = await ai_assistant.ask_ai(charter_question, f"{message.author} ({message.author.id})")
                
                # Step 2: If no charter info, try general AI search
                if ai_response and "NO_CHARTER_INFO" in ai_response:
                    logger.info("No charter info found, trying general AI search")
                    general_question = f"""You are Harry, a friendly CFB 26 league assistant. Answer this question about CFB 26 league rules, recruiting, transfers, or dynasty management:

Question: {question}

IMPORTANT: Only provide a direct answer if you're confident about CFB 26 league specifics. If you're not sure about the exact league rules, say "I don't have that specific information about our league rules, but you can check our full charter for the official details."

Keep responses concise and helpful. Do NOT mention "charter" unless you truly don't know the answer."""

                    # Log the general AI question
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
        description="Available commands for the CFB 26 online dynasty league:",
        color=0x1e90ff
    )
    
    embed.add_field(
        name="/rule <rule_name>",
        value="Look up specific league rules (recruiting, transfers, gameplay, etc.)",
        inline=False
    )
    embed.add_field(
        name="/recruiting <topic>",
        value="Get recruiting rules and policies",
        inline=False
    )
    embed.add_field(
        name="/dynasty <topic>",
        value="Get dynasty management rules (transfers, gameplay, scheduling, conduct)",
        inline=False
    )
    embed.add_field(
        name="/team <team_name>",
        value="Get team information and stats",
        inline=False
    )
    embed.add_field(
        name="/charter",
        value="Get direct link to the official league charter",
        inline=False
    )
    embed.add_field(
        name="/search <term>",
        value="Search for specific terms in the league charter",
        inline=False
    )
    embed.add_field(
        name="/harry <question>",
        value="Ask Harry (the bot) about league rules in a conversational way",
        inline=False
    )
    embed.add_field(
        name="/ask <question>",
        value="Ask AI about league rules and policies (if AI is enabled)",
        inline=False
    )
    embed.add_field(
        name="/help_cfb",
        value="Show this help message",
        inline=False
    )
    
    embed.add_field(
        name="💬 Chat Interactions:",
        value="• Mention me: `@Harry what are the rules?`\n• Ask questions: `What's the transfer policy?`\n• Say hi: `Hi Harry!`\n• React with ❓ to my messages for help",
        inline=False
    )
    
    embed.add_field(
        name="📖 **OFFICIAL LEAGUE CHARTER**", 
        value="[**📋 View Complete Rules & Policies**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)\n\n*This is the official source for all CFB 26 league rules!*",
        inline=False
    )
    
    embed.set_footer(text="CFB 26 League Bot - Ready to help with league rules!")
    
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
            
            # Make the AI response more conversational
            conversational_question = f"Answer this question about CFB 26 league rules in a friendly, conversational way as if you're Harry the league assistant: {question}"
            response = await ai_assistant.ask_ai(conversational_question)
            
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

@bot.tree.command(name="ask", description="Ask AI about league rules and policies")
async def ask_ai(interaction: discord.Interaction, question: str):
    """Ask AI about the league charter"""
    embed = discord.Embed(
        title="🤖 AI Assistant Response",
        color=0x9b59b6
    )
    
    if AI_AVAILABLE and ai_assistant:
        try:
            # Send initial response immediately
            await interaction.response.send_message("🤖 Thinking...", ephemeral=True)
            
            response = await ai_assistant.ask_ai(question)
            if response:
                embed.description = response
                embed.add_field(
                    name="💡 Tip",
                    value="AI responses are based on the league charter. Always verify important rules in the full document.",
                    inline=False
                )
            else:
                embed.description = "Sorry, I couldn't get an AI response right now. Please check the charter directly."
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

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Use `/help_cfb` for command usage.")
    else:
        print(f"Error: {error}")

if __name__ == "__main__":
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
