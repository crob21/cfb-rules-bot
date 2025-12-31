# 📝 Changelog

All notable changes to the CFB 26 Rules Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-12-31

### Added

- **Interactive Charter Updates**
  - Update the charter by talking to Harry naturally
  - `@Harry update the advance time to 10am`
  - `@Harry add a rule: no trading during playoffs`
  - `@Harry change quarter length to 5 minutes`
  - Before/after preview with reaction confirmation (✅/❌)
  - Automatic backup before any change
  - Changelog tracks who changed what and when
  - `/charter_history` command to view recent changes

- **Rule Scanning from Voting Channels**
  - `/scan_rules #channel [hours]` - Scan for rule changes
  - Natural language: `@Harry scan #voting for rule changes`
  - AI identifies passed, failed, and proposed rules
  - Shows vote counts when mentioned in messages
  - React with 📝 to generate charter updates from passed rules
  - Apply all updates with a single confirmation

- **Co-Commissioner Picker**
  - `/pick_commish [hours]` - AI-powered co-commish recommendations
  - Analyzes chat activity and participation
  - 🚨 **ASSHOLE DETECTOR** - rates toxic behavior!
  - Scores: Activity, Helpfulness, Leadership, Drama, Vibes
  - Ranks ALL participants from best to worst
  - Personalized roasts for each candidate
  - Identifies biggest asshole who should NEVER be commish

- **League Staff Tracking**
  - `/league_staff` - View current owner and co-commissioner
  - `/set_league_owner @user` - Set the league owner (Admin)
  - `/set_co_commish @user` - Set the co-commissioner (Admin)
  - Special option: "We don't fucking have one" for co-commish
  - Persists across bot restarts and deployments

- **Schedule Integration**
  - `/schedule [week]` - View matchups for a specific week
  - `/matchup <team> [week]` - Find a team's opponent
  - `/byes [week]` - Show teams with byes
  - Ask Harry naturally: "Who does Hawaii play in week 4?"
  - AI knows current week for "this week" questions

### Changed
- `/pick_commish` uses 2000 tokens for full roasts
- Improved token limit parameters in AI integration
- Better message chunking for long responses

### Fixed
- All bare `except:` blocks replaced with specific exceptions
- Memory leak from pending charter updates (cleanup task added)
- `processed_messages` set now trimmed to prevent unbounded growth
- Discord interaction timeouts with proper defer handling

### Security
- Charter updates require admin permissions
- Rule scanning requires admin permissions
- Reaction-based confirmations prevent accidental changes

## [1.2.0] - 2025-12-29

### Added

- **Dynasty Week System**
  - Full 30-week CFB 26 dynasty season structure
  - Week 0-15: Regular Season
  - Week 16-21: Post-Season (Bowl games, playoffs)
  - Week 22-29: Offseason (Portal, signing day, preseason)
  - `/week` - Show current week and actions
  - `/weeks` - Full 30-week schedule display

- **Week Actions & Notes**
  - Each week shows available actions (staff moves, job offers, etc.)
  - Important notes and deadline reminders
  - Bowl weeks show hiring/firing windows
  - Offseason weeks show portal and recruiting actions

- **Automatic Season Rollover**
  - Preseason (Week 29) advances to Week 0 of next season
  - New season celebration announcement
  - Season counter automatically increments

## [1.1.1] - 2025-11-04

### Added
- **Timer Persistence**
  - Timer state persists across deployments via Discord messages
  - Automatic restoration on bot restart/deployment
  - Falls back to environment variable and file system
  - Persistence status displayed in `/time_status` command

- **Natural Language Features**
  - Commissioner updates via @mention: `@Harry update commish to Wusty`
  - Message relay: `@Harry tell @User to message`
  - Channel summary requests: `@Harry what happened in the last 3 hours?`

- **Focus Parameter for Summaries**
  - Optional focus filter for `/summarize` command
  - Example: `/summarize 24 rules` - filters to rules discussions
  - Enhanced AI prompts for better filtering

### Changed
- `/ask` command now always uses general AI (no league context)
- `/harry` command for league-specific questions
- Improved error handling and logging
- Better deduplication for message processing

### Fixed
- Timer persistence across deployments
- Duplicate message processing race condition
- `/time_status` command interaction timeout
- Focus parameter not working in `/summarize`
- Summary detection for natural language requests

## [1.1.0] - 2025-11-04

### Added
- **Advance Timer**
  - Custom countdown timers (1-336 hours)
  - Automatic reminders at 24h, 12h, 6h, 1h
  - Progress bar with color-coded urgency
  - Commands: `/advance [hours]`, `/time_status`, `/stop_countdown`

- **Channel Summarization**
  - AI-powered channel message summaries
  - Customizable time periods (1-168 hours)
  - Structured output with topics, decisions, participants
  - Command: `/summarize [hours] [focus]`

- **Charter Management**
  - Direct charter editing from Discord
  - Add/update rules with AI formatting
  - Automatic backups before changes
  - View and restore backups
  - Commands: `/add_rule`, `/update_rule`, `/view_charter_backups`, `/restore_charter_backup`

- **Bot Admin System**
  - Manage bot admins via Discord
  - Add/remove/list bot admins
  - Discord Administrators have automatic access
  - Commands: `/add_bot_admin`, `/remove_bot_admin`, `/list_bot_admins`

- **Channel Management**
  - Block/unblock channels for unprompted responses
  - @mentions work everywhere (even in blocked channels)
  - Commands: `/block_channel`, `/unblock_channel`, `/list_blocked_channels`

- **Version Control**
  - `/version` - Show current version
  - `/changelog [version]` - View version history
  - `/whats_new` - Showcase latest features

### Changed
- Guild-specific command sync for instant updates
- Improved admin permission checking
- Better error messages and logging

### Security
- Admin-only commands for timer and charter management
- Hardcoded admin support for permanent admins

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
