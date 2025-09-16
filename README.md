# 🏈 CFB 26 League Bot

A Discord bot for the CFB 26 online dynasty league. Answer questions about league rules, charter, and dynasty management.

## Features

- **League Rules**: Quick access to CFB 26 league charter and rules
- **Dynasty Management**: Help with recruiting, transfers, and league policies
- **Team Information**: League teams, conferences, and standings
- **Interactive Commands**: Slash commands for common league questions

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   ```bash
   cp env.example .env
   # Edit .env with your Discord bot token
   ```

3. **Run the Bot**
   ```bash
   python bot.py
   ```

## Commands

- `/rule <rule_name>` - Look up specific league rule
- `/recruiting <topic>` - Get recruiting rules and policies
- `/team <team_name>` - Get team information
- `/conference <conference_name>` - Get conference information
- `/dynasty <topic>` - Get dynasty management rules
- `/charter` - Get direct link to the official league charter
- `/search <term>` - Search for specific terms in the league charter
- `/ask <question>` - Ask AI about league rules and policies (optional)
- `/help_cfb` - Show all available commands

## Optional Integrations

### AI Integration
Add AI-powered responses to league questions:
- **Setup**: See [AI_SETUP.md](AI_SETUP.md)
- **Providers**: OpenAI GPT or Anthropic Claude
- **Cost**: ~$0.001-0.002 per question

### Google Docs Integration
Direct integration with your league charter:
- **Setup**: See [GOOGLE_DOCS_SETUP.md](GOOGLE_DOCS_SETUP.md)
- **Features**: Search document content, extract sections
- **Requirements**: Google Cloud credentials

## Development

This bot is built with:
- `discord.py` - Discord API wrapper
- `aiohttp` - HTTP client for API calls
- `python-dotenv` - Environment variable management
- `google-api-python-client` - Google Docs integration (optional)
- `openai` / `anthropic` - AI integration (optional)

## License

MIT License
