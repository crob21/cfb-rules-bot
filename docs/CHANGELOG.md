# 📝 Changelog

All notable changes to the CFB 26 Rules Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation and setup guides
- Contributing guidelines and code of conduct
- MIT License
- Changelog for tracking changes

### Changed
- Improved README with better structure and examples
- Enhanced setup guide with step-by-step instructions
- Cleaner code organization and documentation

## [1.0.0] - 2024-09-17

### Added
- **Core Bot Functionality**
  - Discord.py integration with slash commands
  - AI-powered responses using OpenAI GPT-3.5-turbo
  - Google Docs integration for charter content
  - Comprehensive logging system

- **Slash Commands**
  - `/harry <question>` - Ask Harry anything about the league
  - `/ask <question>` - AI-powered league questions
  - `/rule <topic>` - Get specific rule information
  - `/recruiting` - Recruiting rules and policies
  - `/dynasty` - Dynasty management help
  - `/charter` - Link to official league charter
  - `/help_cfb` - Show all available commands

- **Chat Interactions**
  - Natural language processing for questions
  - Automatic detection of league-related keywords
  - Greeting responses and user-friendly interactions
  - Rivalry responses (Oregon sucks! 🦆💩)

- **Emoji Reactions**
  - Interactive responses to emoji reactions
  - Help system via reaction commands
  - Fun, league-specific reactions

- **Deployment**
  - Render deployment configuration
  - Environment variable management
  - Automatic deployment on git push

### Changed
- **Response System**
  - Cleaned up response formatting
  - Removed unnecessary "Responding to" fields
  - Conditional charter links (only when asking about rules)
  - Simplified rivalry responses

- **Logging**
  - Added comprehensive logging for debugging
  - Server information in logs
  - Message content debugging
  - Better error tracking

### Fixed
- **Message Content Intent**
  - Fixed bot not reading message content
  - Enabled proper message content permissions
  - Resolved empty message issues

- **Database Integration**
  - Removed fake/placeholder rules
  - Direct users to official Google Doc charter
  - Clean data structure for league-specific content

### Security
- Environment variable protection
- Secure API key management
- Proper Discord bot permissions

## [0.9.0] - 2024-09-16

### Added
- Initial bot structure and basic commands
- AI integration setup
- Google Docs integration framework
- Basic slash command system

### Changed
- Multiple iterations of response formatting
- Various logging improvements
- Bot permission configurations

### Fixed
- Interaction timeout errors
- Command synchronization issues
- Message content reading problems

## [0.8.0] - 2024-09-15

### Added
- Project organization and structure
- Basic Discord bot setup
- Initial command framework

### Changed
- Repository organization
- File structure improvements

---

## Legend

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
