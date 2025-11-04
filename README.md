# CFB Rules Bot 🏈

A Discord bot for College Football 26 Online Dynasty League that provides league rule information, AI-powered responses, and fun rivalry interactions.

## Features

- 🤖 **AI-Powered Responses** - Get intelligent answers about league rules and policies
- 📋 **League Charter Access** - Quick access to league rules and regulations
- ⏰ **Advance Timer** - 48-hour countdown with automatic reminders at 24h, 12h, 6h, 1h
- 📊 **Channel Summarization** - AI-powered summaries of channel discussions
- 📝 **Charter Management** - Edit and update league rules directly from Discord
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
- `/tokens` - Show AI token usage statistics

#### Advance Timer
- `/advance [hours]` - Start countdown with auto-reminders (default: 48 hours)
  - Example: `/advance` - 48 hour countdown
  - Example: `/advance 24` - 24 hour countdown
  - Example: `/advance 72` - 72 hour countdown
- `/time_status` - Check countdown progress
- `/stop_countdown` - Stop timer (Admin only)

#### Channel Summarization
- `/summarize [hours] [focus]` - Summarize channel activity
  - Example: `/summarize 24` - Last 24 hours
  - Example: `/summarize 48 recruiting` - Last 48h focused on recruiting

#### Charter Management (Admin Only)
- `/add_rule <title> <content>` - Add new rule to charter
- `/update_rule <section> <content>` - Update existing rule
- `/view_charter_backups` - View available backups
- `/restore_charter_backup <file>` - Restore from backup

### Chat Interactions

- **Mention the bot** - `@CFB Bot` or just type `harry` in your message
- **Ask questions** - "What are the recruiting rules?"
- **Get help** - "harry help me with the league rules"

### AI Features

The bot uses AI to provide intelligent responses about league rules and policies. It can:
- Answer specific questions about league rules
- Provide general information about college football
- Help with league management questions

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
