#!/usr/bin/env python3
"""
CFB 26 League Bot - A Discord bot for the CFB 26 online dynasty league
"""

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
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Set up comprehensive logging
def setup_logging():
    """Set up comprehensive logging for Render"""
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

@bot.event
async def on_ready():
    """Called when the bot is ready"""
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
    """Handle regular chat messages"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Comprehensive logging
    guild_name = message.guild.name if message.guild else "DM"
    logger.info(f"📨 Message received: '{message.content}' from {message.author} in #{message.channel} (Server: {guild_name})")
    logger.info(f"📊 Message details: length={len(message.content)}, type={type(message.content)}, repr={repr(message.content)}")
    
    # Skip empty messages
    if not message.content or message.content.strip() == '':
        logger.info(f"⏭️ Skipping empty message from {message.author}")
        return
    
    # Check if the bot is mentioned or if message contains league-related keywords
    bot_mentioned = bot.user.mentioned_in(message)
    league_keywords = ['rule', 'rules', 'charter', 'league', 'recruiting', 'transfer', 'penalty', 'difficulty', 'sim']
    contains_keywords = any(keyword in message.content.lower() for keyword in league_keywords)
    is_question = message.content.strip().endswith('?')
    
    logger.info(f"🔍 Message analysis: bot_mentioned={bot_mentioned}, contains_keywords={contains_keywords}, is_question={is_question}")
    
    # Check for greetings
    greetings = ['hi harry', 'hello harry', 'hey harry', 'harry', 'hi bot', 'hello bot']
    is_greeting = any(greeting in message.content.lower() for greeting in greetings)
    
    # Check for rivalry/fun responses
    rivalry_keywords = {
        'oregon': 'Fuck Oregon! 🦆💩',
        'ducks': 'Ducks are assholes! 🦆💩',
        'rules': 'Here are the CFB 26 league rules! 📋\n\n[📖 **Full League Charter**](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)',
    }
    
    rivalry_response = None
    for keyword, response in rivalry_keywords.items():
        if keyword in message.content.lower():
            rivalry_response = response
            break
    
    logger.info(f"🔍 Response triggers: is_greeting={is_greeting}, rivalry_response={rivalry_response is not None}")
    
    # Respond if mentioned, contains league keywords, is a direct question, is a greeting, or has rivalry keywords
    if bot_mentioned or contains_keywords or is_question or is_greeting or rivalry_response:
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
        
        # Handle rivalry responses specially
        if rivalry_response:
            embed.description = rivalry_response
            embed.add_field(
                name="💬 Responding to:",
                value=f"*{message.content}*",
                inline=False
            )
            embed.add_field(
                name="🏈 CFB 26 League",
                value="Speaking of teams, need help with league rules? Just ask!",
                inline=False
            )
        # Handle greetings specially
        elif is_greeting and not contains_keywords and not is_question:
            embed.description = f"Hi {message.author.display_name}! 👋 I'm Harry, your CFB 26 league assistant! I'm here to help with any questions about league rules, recruiting, transfers, or anything else in our charter. Just ask me anything!"
        elif AI_AVAILABLE and ai_assistant:
            try:
                # Make the question more conversational
                question = message.content
                if bot_mentioned:
                    # Remove the mention from the question
                    question = question.replace(f'<@{bot.user.id}>', '').strip()
                
                # Add context to make it more natural
                conversational_question = f"Answer this question about CFB 26 league rules in a friendly, conversational way as if you're Harry the league assistant: {question}"
                response = await ai_assistant.ask_ai(conversational_question)
                
                if response:
                    embed.description = response
                    # Only add charter link if asking about rules
                    if any(keyword in message.content.lower() for keyword in ['rule', 'rules', 'charter', 'league']):
                        embed.add_field(
                            name="📖 Full League Charter",
                            value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
                            inline=False
                        )
                else:
                    embed.description = "Hi! I'm Harry, your CFB 26 league assistant! I can help with general questions, but for the complete and official rules, please check our charter below!"
                    # Only add charter link if asking about rules
                    if any(keyword in message.content.lower() for keyword in ['rule', 'rules', 'charter', 'league']):
                        embed.add_field(
                            name="📖 Full League Charter",
                            value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
                            inline=False
                        )
            except Exception as e:
                embed.description = f"Hi! I'm Harry, your CFB 26 league assistant! I can help with general questions, but for the complete and official rules, please check our charter below!"
                # Only add charter link if asking about rules
                if any(keyword in message.content.lower() for keyword in ['rule', 'rules', 'charter', 'league']):
                    embed.add_field(
                        name="📖 Full League Charter",
                        value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
                        inline=False
                    )
        else:
            embed.description = "Hi! I'm Harry, your CFB 26 league assistant! I can help with general questions, but for the complete and official rules, please check our charter below!"
            # Only add charter link if asking about rules
            if any(keyword in message.content.lower() for keyword in ['rule', 'rules', 'charter', 'league']):
                embed.add_field(
                    name="📖 Full League Charter",
                    value="[View Complete Rules](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
                    inline=False
                )
        
        embed.set_footer(text="Harry - Your CFB 26 League Assistant 🏈")
        
        # Send the response
        await message.channel.send(embed=embed)
    
    else:
        logger.info(f"❌ Bot will NOT respond to message: '{message.content}' (Server: {guild_name})")
    
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
