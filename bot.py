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

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f'🏈 CFB 26 League Bot ({bot.user}) has connected to Discord!')
    print(f'📊 Connected to {len(bot.guilds)} guilds')
    
    # Load league data
    await load_league_data()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

async def load_league_data():
    """Load league rules and data from JSON files"""
    try:
        with open('data/league_rules.json', 'r') as f:
            bot.league_data = json.load(f)
        print("✅ League data loaded successfully")
    except FileNotFoundError:
        print("⚠️  League data file not found - using default data")
        bot.league_data = {"league_info": {"name": "CFB 26 Online Dynasty"}}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing league data: {e}")
        bot.league_data = {"league_info": {"name": "CFB 26 Online Dynasty"}}

@bot.tree.command(name="rule", description="Look up CFB 26 league rules")
async def rule(interaction: discord.Interaction, rule_name: str):
    """Look up a specific league rule"""
    await interaction.response.defer()
    
    # Search for rule in league data
    rule_found = False
    embed = discord.Embed(
        title=f"CFB 26 League Rule: {rule_name.title()}",
        color=0x1e90ff
    )
    
    # Search through league rules
    if hasattr(bot, 'league_data') and 'rules' in bot.league_data:
        for category, rules in bot.league_data['rules'].items():
            if rule_name.lower() in category.lower():
                embed.description = rules.get('description', 'Rule information available')
                if 'topics' in rules:
                    topics_text = '\n'.join([f"• {topic}" for topic in rules['topics'].keys()])
                    embed.add_field(name="Related Topics", value=topics_text, inline=False)
                rule_found = True
                break
    
    if not rule_found:
        embed.description = "Rule not found in league data. Check the league charter for more details."
        embed.add_field(
            name="League Charter", 
            value="[View Full Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
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
        name="/help_cfb",
        value="Show this help message",
        inline=False
    )
    
    embed.add_field(
        name="League Charter", 
        value="[View Full Charter](https://docs.google.com/document/d/1lX28DlMmH0P77aficBA_1Vo9ykEm_bAroSTpwMhWr_8/edit)",
        inline=False
    )
    
    embed.set_footer(text="CFB 26 League Bot - Ready to help with league rules!")
    
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

if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in environment variables")
        print("📝 Please create a .env file with your bot token")
        exit(1)
    
    print("🚀 Starting CFB Rules Bot...")
    bot.run(token)
