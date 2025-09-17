# CFB Rules Bot - Project Structure

## Overview
A Discord bot for College Football 26 Online Dynasty League that provides league rule information, AI-powered responses, and fun rivalry interactions.

## Directory Structure

```
cfb-rules-bot/
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── runtime.txt                 # Python version specification
├── README.md                   # Project documentation
├── PROJECT_STRUCTURE.md        # This file
│
├── src/cfb_bot/               # Main bot package
│   ├── __init__.py            # Package initialization
│   ├── ai/                    # AI integration modules
│   │   ├── __init__.py
│   │   └── ai_integration.py  # OpenAI/Anthropic integration
│   ├── integrations/          # External service integrations
│   │   ├── __init__.py
│   │   └── google_docs_integration.py
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── audioop_fix.py     # Python 3.13 compatibility fix
│       └── update_rules.py    # Rule update utilities
│
├── config/                    # Configuration files
│   ├── env.example           # Environment variables template
│   ├── render.yaml           # Render deployment config
│   ├── railway.json          # Railway deployment config
│   └── Procfile              # Process file for deployment
│
├── data/                     # Data files
│   ├── charter_content.txt   # League charter content
│   ├── league_rules.json     # League rules data
│   ├── penalties.json        # Penalty information
│   └── rules.json            # General rules data
│
├── tests/                    # Test files
│   ├── unit/                 # Unit tests
│   │   ├── test_ai.py
│   │   ├── test_google_docs.py
│   │   └── test_bot.py
│   └── integration/          # Integration tests (empty)
│
├── docs/                     # Documentation
│   ├── api/                  # API documentation (empty)
│   ├── deployment/           # Deployment guides (empty)
│   ├── AI_SETUP.md          # AI setup instructions
│   ├── GOOGLE_DOCS_SETUP.md # Google Docs setup
│   ├── SETUP.md             # General setup
│   ├── CHANGELOG.md         # Version history
│   └── CONTRIBUTING.md      # Contribution guidelines
│
├── scripts/                  # Utility scripts
│   ├── setup.py             # Setup script
│   └── setup_google_docs.py # Google Docs setup script
│
└── logs/                    # Log files
    └── bot.log              # Bot runtime logs
```

## Key Files

### Main Entry Point
- `main.py` - Main entry point that imports and runs the bot

### Core Bot
- `src/cfb_bot/__init__.py` - Main bot logic and Discord integration

### AI Integration
- `src/cfb_bot/ai/ai_integration.py` - OpenAI and Anthropic API integration

### External Integrations
- `src/cfb_bot/integrations/google_docs_integration.py` - Google Docs API integration

### Configuration
- `config/env.example` - Environment variables template
- `config/render.yaml` - Render deployment configuration
- `config/railway.json` - Railway deployment configuration

### Data
- `data/charter_content.txt` - League charter content (markdown format)
- `data/league_rules.json` - Structured league rules
- `data/penalties.json` - Penalty information
- `data/rules.json` - General rules data

## Setup

1. Copy `config/env.example` to `.env` and fill in your API keys
2. Install dependencies: `pip install -r requirements.txt`
3. Run the bot: `python main.py`

## Deployment

The bot is configured for deployment on:
- **Render** (primary) - Uses `config/render.yaml` and `config/Procfile`
- **Railway** (alternative) - Uses `config/railway.json`

## Features

- League rule information and charter access
- AI-powered responses about league policies
- Fun rivalry responses for specific teams
- Team and player information
- Slash commands for easy interaction
- Comprehensive logging and error handling
