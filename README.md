# CFB Rules Bot 🏈

A Discord bot for College Football 26 Online Dynasty League that provides league rule information, AI-powered responses, interactive charter management, and fun rivalry interactions.

## Features

### Core Features
- 🤖 **AI-Powered Responses** - Get intelligent answers about league rules and policies
- 📋 **League Charter Access** - Quick access to league rules and regulations
- ⏰ **Advance Timer** - Custom countdown timers with automatic reminders (persists across deployments!)
- 📅 **Dynasty Week Tracking** - Full 30-week CFB 26 season structure with actions and notes

### Charter Management
- 📝 **Interactive Charter Updates** - Update the charter by talking to Harry naturally
- 🔍 **Rule Scanning** - Scan voting channels for passed rules and apply to charter
- 📜 **Charter History** - Track who changed what and when
- 💾 **Auto-Backup** - Automatic backups before any charter change

### League Management
- 👔 **League Staff Tracking** - Track league owner and co-commissioner
- 👑 **Co-Commish Picker** - AI analyzes chat to recommend new co-commissioners (with asshole detector!)
- 📊 **Channel Summarization** - AI-powered summaries of channel discussions
- 📅 **Schedule Integration** - Ask Harry about matchups and byes

### Bot Administration
- 🔐 **Bot Admin System** - Separate admin permissions for bot-specific features
- 🔇 **Channel Management** - Control where Harry makes unprompted responses
- 📨 **Message Relay** - Relay messages between users

### Fun Features
- 😄 **Rivalry Responses** - Engaging interactions (Fuck Oregon! 🦆💩)
- ⚡ **Slash Commands** - Easy-to-use Discord slash commands
- 🔍 **Smart Filtering** - Only responds to relevant league-related questions

## Quick Start

### Prerequisites

- Python 3.11+ (3.13 recommended)
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

## Commands

### League Information
| Command | Description |
|---------|-------------|
| `/harry <question>` | Ask Harry league-specific questions |
| `/ask <question>` | Ask Harry general questions (not league-specific) |
| `/charter` | Link to the full league charter |
| `/rules` | Get league rules information |
| `/help_cfb` | Show available commands |

### Dynasty Week System
| Command | Description |
|---------|-------------|
| `/week` | Show current week, phase, and actions |
| `/weeks` | Show full 30-week dynasty schedule |
| `/set_season_week <season> <week>` | Set current season and week (Admin) |

### Advance Timer
| Command | Description |
|---------|-------------|
| `/advance [hours]` | Start countdown (default 48h) - Admin only |
| `/time_status` | Check countdown progress |
| `/stop_countdown` | Stop the timer - Admin only |
| `@everyone Advanced` | Quick restart (Admin) |

### Schedule
| Command | Description |
|---------|-------------|
| `/schedule [week]` | Show matchups for a week |
| `/matchup <team> [week]` | Find a team's opponent |
| `/byes [week]` | Show bye teams for a week |

### League Staff
| Command | Description |
|---------|-------------|
| `/league_staff` | Show current owner and co-commish |
| `/set_league_owner @user` | Set the league owner (Admin) |
| `/set_co_commish @user` | Set the co-commissioner (Admin) |
| `/pick_commish [hours]` | AI picks a new co-commish! (Admin) |

### Interactive Charter Updates
| Command | Description |
|---------|-------------|
| `@Harry update <rule>` | Update charter via natural language |
| `/scan_rules #channel [hours]` | Scan for rule changes (Admin) |
| `/charter_history` | View recent charter changes |
| `/add_rule <title> <content>` | Add new rule (Admin) |
| `/update_rule <section> <content>` | Update existing rule (Admin) |

**Examples:**
```
@Harry update the advance time to 10am EST
@Harry add a rule: no trading during playoffs
@Harry change quarter length to 5 minutes
@Harry scan #offseason-voting for rule changes
```

### Channel Summarization
| Command | Description |
|---------|-------------|
| `/summarize [hours] [focus]` | Summarize channel activity |
| `@Harry what happened in the last 3 hours?` | Natural language summary |

### Bot Administration
| Command | Description |
|---------|-------------|
| `/add_bot_admin @user` | Add a bot admin |
| `/remove_bot_admin @user` | Remove a bot admin |
| `/list_bot_admins` | List all bot admins |
| `/block_channel #channel` | Block unprompted responses |
| `/unblock_channel #channel` | Allow unprompted responses |
| `/list_blocked_channels` | Show blocked channels |

### Version & Info
| Command | Description |
|---------|-------------|
| `/whats_new` | See latest features |
| `/version` | Show current version |
| `/changelog [version]` | View version history |

## Dynasty Week Structure

The bot tracks a full 30-week CFB 26 dynasty season:

### Regular Season (Weeks 0-15)
- Week 0: Season Kickoff
- Weeks 1-12: Regular Season
- Week 13: Rivalry Week
- Week 14: Conference Championship Prep
- Week 15: Conference Championships

### Post-Season (Weeks 16-21)
- Week 16: Bowl Week 1 (12-team playoff begins)
- Week 17: Bowl Week 2
- Week 18: Bowl Week 3
- Week 19: Bowl Week 4 (Championship)
- Week 20: End of Season Recap
- Week 21: Award Show

### Offseason (Weeks 22-29)
- Week 22: Portal Week 1
- Week 23: Portal Week 2
- Week 24: Portal Week 3
- Week 25: Portal Week 4 (Portal closes)
- Week 26: National Signing Day
- Week 27: Training Results
- Week 28: Encourage Transfers
- Week 29: Preseason → New Season!

## AI Features

The bot uses AI to provide intelligent responses:

- **League Questions** - `/harry` uses charter context
- **General Questions** - `/ask` for non-league topics
- **Channel Summaries** - AI-powered discussion summaries
- **Charter Updates** - Natural language rule parsing
- **Co-Commish Picker** - Analyzes chat for recommendations

### The Asshole Detector 🚨

The `/pick_commish` command includes Harry's famous asshole detector:
- Activity Level
- Helpfulness
- Leadership
- **Asshole Score** (Are they a dick?)
- Drama Score
- Vibes/Humor
- Reliability
- Knowledge

## Project Structure

```
cfb-rules-bot/
├── main.py                     # Main entry point
├── src/cfb_bot/               # Main bot package
│   ├── bot.py                 # Discord bot logic
│   ├── ai/                    # AI integration
│   ├── integrations/          # External services
│   └── utils/                 # Utility functions
│       ├── timekeeper.py      # Timer & week tracking
│       ├── charter_editor.py  # Charter management
│       ├── schedule_manager.py # Schedule data
│       └── summarizer.py      # Channel summaries
├── config/                    # Configuration files
├── data/                      # Data files
│   ├── charter_content.txt    # League charter
│   ├── schedule.json          # Season schedule
│   └── charter_changelog.json # Update history
├── tests/                     # Test files
├── docs/                      # Documentation
└── scripts/                   # Utility scripts
```

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support or questions:
- Create an issue on GitHub
- Contact the league administrators
- Check the documentation in the `docs/` folder

## Changelog

See [CHANGELOG.md](docs/CHANGELOG.md) for version history and updates.
