# 🚀 CFB 26 Rules Bot Setup Guide

This guide will walk you through setting up Harry, the CFB 26 Rules Bot, from scratch.

## 📋 Prerequisites

Before you begin, you'll need:

- A Discord account
- A Discord server where you have admin permissions
- A GitHub account (for deployment)
- An OpenAI account (optional, for AI features)
- A Google account (optional, for charter integration)

## 🔧 Step 1: Discord Bot Setup

### 1.1 Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Give your bot a name (e.g., "CFB 26 Rules Bot")
4. Click **"Create"**

### 1.2 Create the Bot

1. In your application, go to the **"Bot"** section
2. Click **"Add Bot"**
3. Customize your bot:
   - **Username**: `CFB Bot` or `Harry`
   - **Avatar**: Upload a football-themed image
   - **Description**: "CFB 26 League Assistant"

### 1.3 Configure Bot Permissions

1. In the **"Bot"** section, scroll down to **"Privileged Gateway Intents"**
2. Enable the following intents:
   - ✅ **MESSAGE CONTENT INTENT** (required for reading messages)
   - ✅ **SERVER MEMBERS INTENT** (for user information)

### 1.4 Get Your Bot Token

1. In the **"Bot"** section, click **"Reset Token"**
2. Copy the token (keep it secret!)
3. Save it for later use

### 1.5 Get Your Server ID

1. In Discord, go to **User Settings** → **Advanced**
2. Enable **"Developer Mode"**
3. Right-click on your server name
4. Click **"Copy Server ID"**

## 🔑 Step 2: API Keys (Optional)

### 2.1 OpenAI API Key (Recommended)

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in
3. Go to **"API Keys"**
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-`)

### 2.2 Google Docs API (Advanced)

If you want to integrate with your league charter:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable the **Google Docs API**
4. Create credentials (Service Account)
5. Download the JSON key file

## 💻 Step 3: Local Development Setup

### 3.1 Clone the Repository

```bash
git clone https://github.com/crob21/cfb-rules-bot.git
cd cfb-rules-bot
```

### 3.2 Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3.3 Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file with your tokens
nano .env  # or use your preferred editor
```

**Required variables:**
```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_server_id_here
```

**Optional variables:**
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3.4 Test the Bot Locally

```bash
python3 bot.py
```

You should see:
```
🏈 CFB 26 League Bot (CFB Bot#1109) has connected to Discord!
📊 Connected to 1 guilds
👋 Harry is ready to help with league questions!
✅ Synced 9 command(s)
```

## 🚀 Step 4: Deploy to Render

### 4.1 Connect to Render

1. Go to [Render](https://render.com)
2. Sign up with your GitHub account
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository

### 4.2 Configure the Service

**Basic Settings:**
- **Name**: `cfb-rules-bot`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 bot.py`

**Environment Variables:**
Add all your environment variables from the `.env` file:
- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `OPENAI_API_KEY` (optional)
- `ANTHROPIC_API_KEY` (optional)

### 4.3 Deploy

1. Click **"Create Web Service"**
2. Wait for the build to complete
3. Check the logs to ensure the bot connects successfully

## 🔗 Step 5: Invite Bot to Your Server

### 5.1 Generate Invite URL

1. Go back to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to **"OAuth2"** → **"URL Generator"**

### 5.2 Configure Permissions

**Scopes:**
- ✅ `bot`
- ✅ `applications.commands`

**Bot Permissions:**
- ✅ `Send Messages`
- ✅ `Use Slash Commands`
- ✅ `Read Message History`
- ✅ `Add Reactions`
- ✅ `Embed Links`
- ✅ `View Channels`
- ✅ `Send Messages in Threads`

### 5.3 Invite the Bot

1. Copy the generated URL
2. Paste it in your browser
3. Select your server
4. Click **"Authorize"**

## ✅ Step 6: Test Your Bot

### 6.1 Test Slash Commands

In your Discord server, try:
- `/harry what are the league rules?`
- `/ask how does recruiting work?`
- `/help_cfb`

### 6.2 Test Chat Interactions

Try these messages:
- `@Harry what are the rules?`
- `Hi Harry!`
- `Oregon sucks!`
- `How does recruiting work?`

### 6.3 Test Emoji Reactions

1. Send a message to Harry
2. React with `❓` to get help
3. React with `🏈` for football responses

## 🔧 Troubleshooting

### Common Issues

**Bot not responding to messages:**
- Check that `MESSAGE CONTENT INTENT` is enabled
- Verify the bot has `View Channels` permission
- Check Render logs for errors

**Slash commands not working:**
- Ensure `applications.commands` scope is selected
- Wait a few minutes for commands to sync
- Try restarting the bot

**AI features not working:**
- Verify your OpenAI API key is correct
- Check that you have credits in your OpenAI account
- Look for API errors in the logs

### Getting Help

- Check the [GitHub Issues](https://github.com/crob21/cfb-rules-bot/issues)
- Review the [README](README.md) for more information
- Contact the league commissioners

## 🎉 You're Done!

Your CFB 26 Rules Bot is now set up and ready to help your league members! Harry will:

- Answer questions about league rules
- Provide AI-powered responses
- React to Oregon mentions with rivalry responses
- Help with recruiting and transfer questions
- Link to the official league charter

**Welcome to the CFB 26 League! 🏈**
