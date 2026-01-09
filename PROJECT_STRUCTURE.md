# CFB Rules Bot - Project Structure

## Overview

A Discord bot for College Football 26 Online Dynasty League that provides league rule information, AI-powered responses, CFB data lookups, and fun rivalry interactions.

**Current Version:** 1.14.0  
**Codename:** Harry

## Directory Structure

```
cfb-rules-bot/
├── main.py                     # Main entry point
├── run_dashboard.py            # Dashboard server entry point
├── requirements.txt            # Python dependencies
├── runtime.txt                 # Python version specification
├── README.md                   # Project documentation
├── PROJECT_STRUCTURE.md        # This file
│
├── src/
│   ├── cfb_bot/               # Main bot package
│   │   ├── __init__.py        # Package initialization
│   │   ├── bot.py             # Discord bot logic & commands
│   │   │
│   │   ├── ai/                # AI integration modules
│   │   │   ├── __init__.py
│   │   │   └── ai_integration.py  # OpenAI/Anthropic integration
│   │   │
│   │   ├── integrations/      # External service integrations
│   │   │   ├── __init__.py
│   │   │   └── google_docs_integration.py
│   │   │
│   │   └── utils/             # Utility modules
│   │       ├── __init__.py
│   │       ├── admin_check.py      # Bot admin management
│   │       ├── audioop_fix.py      # Python 3.13 compatibility
│   │       ├── channel_manager.py  # Channel blocking
│   │       ├── charter_editor.py   # Charter management
│   │       ├── player_lookup.py    # CFB player data (CFBD API)
│   │       ├── schedule_manager.py # Schedule data
│   │       ├── server_config.py    # Per-server configuration
│   │       ├── storage.py          # Storage abstraction layer
│   │       ├── summarizer.py       # Channel summaries
│   │       ├── timekeeper.py       # Timer & dynasty weeks
│   │       ├── update_rules.py     # Rule update utilities
│   │       └── version_manager.py  # Version & changelog
│   │
│   └── dashboard/             # Web dashboard
│       ├── __init__.py
│       ├── app.py             # FastAPI application
│       ├── auth.py            # Discord OAuth2
│       ├── routes.py          # API routes
│       ├── static/            # CSS, JS assets
│       │   ├── css/
│       │   └── js/
│       └── templates/         # Jinja2 HTML templates
│           ├── base.html
│           ├── dashboard.html
│           ├── login.html
│           └── server.html
│
├── config/                    # Configuration files
│   ├── env.example           # Environment variables template
│   ├── render.yaml           # Render deployment config
│   ├── railway.json          # Railway deployment config
│   └── Procfile              # Process file for deployment
│
├── data/                     # Data files
│   ├── charter_content.txt   # League charter content
│   ├── charter_changelog.json # Charter change history
│   ├── league_rules.json     # League rules data
│   ├── penalties.json        # Penalty information
│   ├── rules.json            # General rules data
│   └── schedule.json         # Season schedule
│
├── tests/                    # Test files
│   ├── unit/                 # Unit tests
│   │   ├── test_ai.py
│   │   ├── test_bot.py
│   │   └── test_google_docs.py
│   └── integration/          # Integration tests
│
├── docs/                     # Documentation
│   ├── README.md            # Docs overview
│   ├── AI_SETUP.md          # AI setup instructions
│   ├── CHANGELOG.md         # Version history
│   ├── CONTRIBUTING.md      # Contribution guidelines
│   ├── GOOGLE_DOCS_SETUP.md # Google Docs setup
│   ├── NEW_FEATURES.md      # Feature documentation
│   ├── SETUP.md             # General setup guide
│   ├── TIMER_PERSISTENCE_TESTING.md
│   ├── VERSION_MANAGEMENT.md # Version guide
│   ├── api/                  # API documentation
│   └── deployment/           # Deployment guides
│
├── scripts/                  # Utility scripts
│   ├── setup.py             # Setup script
│   └── setup_google_docs.py # Google Docs setup script
│
└── logs/                    # Log files
    └── bot.log              # Bot runtime logs
```

## Key Modules

### Core Bot (`src/cfb_bot/bot.py`)
Main Discord bot with:
- Slash commands
- Event handlers (messages, reactions)
- Natural language processing
- Module system integration

### Storage (`src/cfb_bot/utils/storage.py`)
Pluggable storage backends:
- `DiscordDMStorage` - Free, stores in bot owner's DMs
- `SupabaseStorage` - PostgreSQL for scaling

### Server Config (`src/cfb_bot/utils/server_config.py`)
Per-server feature configuration:
- Module enable/disable (Core, CFB Data, League)
- Per-channel controls
- Auto-response toggles
- Personality settings

### Player Lookup (`src/cfb_bot/utils/player_lookup.py`)
CFB player data via CollegeFootballData.com:
- Player vitals and stats
- Recruiting information
- Transfer portal data
- Fuzzy matching for suggestions

### Timekeeper (`src/cfb_bot/utils/timekeeper.py`)
Advance timer and dynasty week tracking:
- Countdown management
- Automatic notifications
- 30-week season structure
- Persistence via storage system

### Dashboard (`src/dashboard/`)
Web interface for configuration:
- FastAPI backend
- Discord OAuth2 authentication
- Module management UI
- Bot admin management

## Configuration

### Environment Variables

```env
# Required
DISCORD_BOT_TOKEN=xxx

# Optional AI
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx

# Optional CFB Data
CFB_DATA_API_KEY=xxx

# Storage Backend
STORAGE_BACKEND=discord  # or supabase

# Supabase (if scaling)
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
```

### Feature Modules

| Module | Description | Default |
|--------|-------------|---------|
| Core | Personality, AI, management | Always On |
| CFB Data | Player lookup, rankings | Enabled |
| League | Timer, charter, dynasty | Disabled |

## Deployment

### Render (Recommended)
Uses `config/render.yaml` and `config/Procfile`

### Railway
Uses `config/railway.json`

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot
python main.py

# Run dashboard
python run_dashboard.py

# Run tests
python -m pytest tests/
```

---

**Version:** 1.13.0  
**Last Updated:** January 9, 2026
