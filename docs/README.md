# 🏈 CFB 26 Rules Bot

> **Harry** - Your intelligent Discord assistant for the CFB 26 online dynasty league

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-green.svg)](https://discordpy.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Render-00d4aa.svg)](https://render.com)

A sophisticated Discord bot designed specifically for the CFB 26 online dynasty league. Harry combines AI-powered responses with league-specific knowledge to help members navigate rules, recruiting, transfers, and more.

## ✨ Features

### 🤖 **AI-Powered Assistant**
- **Natural Language Processing**: Ask questions in plain English
- **OpenAI Integration**: Powered by GPT-3.5-turbo for intelligent responses
- **Context-Aware**: Understands league-specific terminology and rules

### 🏈 **League-Specific Commands**
- **Slash Commands**: `/harry`, `/ask`, `/rule`, `/recruiting`, `/dynasty`
- **Smart Responses**: Automatically detects questions about rules, recruiting, transfers
- **Charter Integration**: Direct links to official league charter

### 💬 **Conversational AI**
- **Chat Interactions**: Responds to mentions, questions, and greetings
- **Rivalry Responses**: Fun, league-specific reactions (Oregon sucks! 🦆💩)
- **Emoji Reactions**: Interactive responses to reactions on messages

### 📊 **Comprehensive Logging**
- **Detailed Logs**: Track all interactions and responses
- **Server Information**: Know which server interactions come from
- **Debug Support**: Easy troubleshooting and monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Discord Bot Token
- OpenAI API Key (optional, for AI features)
- Google Docs API credentials (optional, for charter integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/crob21/cfb-rules-bot.git
   cd cfb-rules-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your tokens and keys
   ```

4. **Run the bot**
   ```bash
   python3 bot.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_BOT_TOKEN` | Your Discord bot token | ✅ |
| `DISCORD_GUILD_ID` | Your Discord server ID | ✅ |
| `OPENAI_API_KEY` | OpenAI API key for AI features | ❌ |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative) | ❌ |

### Discord Bot Setup

1. **Create a Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot

2. **Enable Required Intents**
   - ✅ `MESSAGE CONTENT INTENT` (required for reading messages)
   - ✅ `SERVER MEMBERS INTENT` (for user information)

3. **Generate Invite URL**
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Use Slash Commands`, `Read Message History`, `Add Reactions`, `Embed Links`, `View Channels`

## 📖 Usage

### Slash Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/harry <question>` | Ask Harry anything about the league | `/harry what are the recruiting rules?` |
| `/ask <question>` | AI-powered league question | `/ask how do transfers work?` |
| `/rule <topic>` | Get specific rule information | `/rule recruiting` |
| `/recruiting` | Recruiting rules and policies | `/recruiting` |
| `/dynasty` | Dynasty management help | `/dynasty` |
| `/charter` | Link to official league charter | `/charter` |
| `/help_cfb` | Show all available commands | `/help_cfb` |

### Chat Interactions

Harry responds to natural conversation:

- **Mentions**: `@Harry what are the rules?`
- **Questions**: `How does recruiting work?`
- **Greetings**: `Hi Harry!`
- **Rivalry**: `Oregon sucks!` → `Fuck Oregon! 🦆💩`

### Emoji Reactions

React to Harry's messages with:
- `❓` - Get help and command list
- `🏈` - Football-related responses
- `🦆` - Oregon-related responses
- `🐕` - Team spirit responses

## 🏗️ Architecture

### Project Structure

```
cfb-rules-bot/
├── bot.py                 # Main bot application
├── ai_integration.py      # AI service integration
├── google_docs_integration.py  # Google Docs API
├── data/
│   ├── league_rules.json  # League-specific rules
│   ├── rules.json         # General rules (empty)
│   └── penalties.json     # Penalties (empty)
├── logs/                  # Log files
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
├── Procfile              # Render deployment
├── render.yaml           # Render configuration
└── README.md             # This file
```

### Key Components

- **`bot.py`**: Main Discord bot with event handlers and slash commands
- **`ai_integration.py`**: OpenAI/Anthropic API integration for intelligent responses
- **`google_docs_integration.py`**: Google Docs API for charter content
- **Data files**: League-specific configuration and rules

## 🚀 Deployment

### Render (Recommended)

1. **Connect GitHub repository** to Render
2. **Create a new Web Service**
3. **Configure environment variables**
4. **Deploy automatically** on git push

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DISCORD_BOT_TOKEN="your_token"
export OPENAI_API_KEY="your_key"

# Run the bot
python3 bot.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CFB 26 League**: For providing the charter and rules
- **Discord.py**: For the excellent Discord API wrapper
- **OpenAI**: For the AI capabilities
- **Render**: For hosting the bot

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/crob21/cfb-rules-bot/issues)
- **Discord**: Contact league commissioners
- **Documentation**: [Wiki](https://github.com/crob21/cfb-rules-bot/wiki)

---

**Made with ❤️ for the CFB 26 League**

*Harry is always here to help with your dynasty questions! 🏈*