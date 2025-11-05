# CFB Rules Bot 🏈

A Discord bot for College Football 26 Online Dynasty League that provides league rule information, AI-powered responses, and fun rivalry interactions.

## Features

- 🤖 **AI-Powered Responses** - Get intelligent answers about league rules and policies
- 📋 **League Charter Access** - Quick access to league rules and regulations
- ⏰ **Advance Timer** - Custom countdown timers with automatic reminders (persists across deployments!)
- 📊 **Channel Summarization** - AI-powered summaries of channel discussions with optional focus
- 📝 **Charter Management** - Edit and update league rules directly from Discord
- 👔 **Commissioner Updates** - Natural language updates to league officers
- 🔇 **Channel Management** - Control where Harry makes unprompted responses (@mentions work everywhere)
- 🔐 **Bot Admin System** - Separate admin permissions for bot-specific features
- 📨 **Message Relay** - Relay messages between users
- 🏆 **Team Information** - Player rosters, team histories, and league standings
- 😄 **Fun Interactions** - Rivalry responses and engaging conversations
- ⚡ **Slash Commands** - Easy-to-use Discord slash commands
- 🔍 **Smart Filtering** - Only responds to relevant league-related questions

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- OpenAI API Key (optional, for AI features)
- Anthropic API Key (optional, for AI features)

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
   cp config/env.example .env
   # Edit .env with your API keys
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Optional (for AI features)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (for Google Docs integration)
GOOGLE_DOCS_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_DOCS_DOCUMENT_ID=your_document_id_here
```

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable the following intents:
   - Message Content Intent
   - Server Members Intent
6. Invite the bot to your server with appropriate permissions

## Usage

### Slash Commands

#### Core Commands
- `/help_cfb` - Show available commands
- `/rules` - Get league rules information
- `/charter` - Link to the full league charter
- `/harry <question>` - Ask Harry league-specific questions
- `/ask <question>` - Ask Harry general questions (not league-specific)
- `/tokens` - Show AI token usage statistics

#### Advance Timer (Admin Only)
- `/advance [hours]` - Start countdown with auto-reminders **(Admin only)**
  - Example: `/advance` - 48 hour countdown (default)
  - Example: `/advance 24` - 24 hour countdown
  - Example: `/advance 72` - 72 hour countdown
  - **Persistence**: Timer state persists across deployments via Discord messages!
- `/time_status` - Check countdown progress (Anyone can view)
  - Shows time remaining, progress bar, and persistence status
- `/stop_countdown` - Stop timer **(Admin only)**
- **Quick Restart**: `@everyone Advanced` or `@here advance` (Admin only)
  - Mentions @everyone/@here + "advanced"/"advance" (case-insensitive)
  - Automatically stops current timer and starts new 48-hour countdown
  - Example: `@everyone we've advanced!` will restart the timer
  - Example: `@here ADVANCED` will restart the timer

#### Channel Summarization
- `/summarize [hours] [focus]` - Summarize channel activity
  - Example: `/summarize 24` - Last 24 hours
  - Example: `/summarize 48 recruiting` - Last 48h focused on recruiting
  - Example: `/summarize 24 rules` - Last 24h focused on rules discussions
  - `hours` (optional, default: 24): 1-168 hours
  - `focus` (optional): Filter summary to specific topic
- **Natural Language**: `@Harry what happened in this channel for the last 3 hours?`
  - Detects summary requests via @mention
  - Automatically extracts time period from question

#### Charter Management (Admin Only)
- `/add_rule <title> <content>` - Add new rule to charter
- `/update_rule <section> <content>` - Update existing rule
- `/view_charter_backups` - View available backups
- `/restore_charter_backup <file>` - Restore from backup

#### Natural Language Features
- **Commissioner Updates**: `@Harry update the league commish to Wusty`
  - Supports multiple phrasings: update/change/set/make commish
  - Handles @mentions: `@Harry update commish to @Wusty`
  - Admin-only feature
  - Automatically backs up charter before updating
- **Message Relay**: `@Harry tell @User to message`
  - Relay messages between users
  - Example: `@Harry tell @wustyman to fuck off`
- **Channel Summaries**: `@Harry what happened in this channel for the last 3 hours?`
  - Natural language summary requests
  - Automatically extracts time period
  - Works in any channel where @Harry is mentioned

#### Bot Admin Management
- `/add_bot_admin @user` - Add a user as bot admin **(Admin only)**
- `/remove_bot_admin @user` - Remove a user as bot admin **(Admin only)**
- `/list_bot_admins` - List all bot admins

#### Channel Management (Admin Only)
- `/block_channel #channel` - Block unprompted responses in a channel
- `/unblock_channel #channel` - Allow unprompted responses in a channel
- `/list_blocked_channels` - Show all blocked channels

**How It Works:**
- **@mentions always work** - Harry responds when mentioned, even in blocked channels
- **No unprompted replies** - Harry won't jump into conversations in blocked channels
- **Slash commands work** - All `/` commands function normally in blocked channels

#### Version & Info
- `/whats_new` - See latest features and updates
- `/version` - Show current bot version
- `/changelog [version]` - View version history
  - Example: `/changelog` - All versions summary
  - Example: `/changelog 1.1.0` - Details for v1.1.0

### Chat Interactions

- **Mention the bot** - `@Harry` works in **any channel** (even blocked ones)
- **Ask questions** - "What are the recruiting rules?"
- **Natural language commands**:
  - `@Harry update the league commish to Wusty` - Update commissioner (admin only)
  - `@Harry tell @User to message` - Relay messages
  - `@Harry what happened in this channel for the last 3 hours?` - Channel summary
- **Get help** - "harry help me with the league rules"
- **Unprompted responses** - Only in channels that allow them (use `/block_channel` to control)

### AI Features

The bot uses AI to provide intelligent responses about league rules and policies. It can:
- Answer specific questions about league rules (via `/harry`)
- Provide general information (via `/ask` - no league context)
- Summarize channel discussions with optional focus
- Format charter rules professionally
- Natural language understanding for commands

**Note**: `/ask` always provides general AI answers without league charter context. Use `/harry` for league-specific questions.

## Project Structure

```
cfb-rules-bot/
├── main.py                     # Main entry point
├── src/cfb_bot/               # Main bot package
│   ├── bot.py                 # Discord bot logic
│   ├── ai/                    # AI integration
│   ├── integrations/          # External services
│   └── utils/                 # Utility functions
├── config/                    # Configuration files
├── data/                      # Data files
├── tests/                     # Test files
├── docs/                      # Documentation
└── scripts/                   # Utility scripts
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information.

## Deployment

### Render (Recommended)

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment Variables**: Add your API keys

### Railway

1. Connect your GitHub repository to Railway
2. Deploy automatically
3. Add environment variables in the Railway dashboard

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. Use a formatter like `black` for consistent formatting.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support or questions:
- Create an issue on GitHub
- Contact the league administrators
- Check the documentation in the `docs/` folder

## Changelog

See [CHANGELOG.md](docs/CHANGELOG.md) for version history and updates.
