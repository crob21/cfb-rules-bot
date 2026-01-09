# 📝 Changelog

All notable changes to the CFB 26 Rules Bot (Harry) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.13.0] - 2026-01-09

### Added

- **Storage Abstraction Layer**
  - Pluggable storage backends for future-proofing
  - `StorageBackend` abstract base class
  - `DiscordDMStorage` - Current free storage (good for <10 servers)
  - `SupabaseStorage` - Placeholder for PostgreSQL scaling
  - `STORAGE_BACKEND` environment variable to switch backends
  - Easy migration path: set env var, deploy, done!

### Changed
- `ServerConfigManager` now uses storage abstraction
- Storage selection via factory pattern (`get_storage()`)

## [1.12.0] - 2026-01-09

### Added

- **Per-Channel Controls**
  - `/channel` command to manage where Harry responds
  - Channel whitelist system - enable specific channels only
  - Per-channel auto-response toggles
  - Harry stays silent in non-whitelisted channels by default

- **Channel Commands**
  - `/channel view` - See current channel settings
  - `/channel enable` - Add channel to whitelist
  - `/channel disable` - Remove from whitelist
  - `/channel disable_all` - Clear whitelist
  - `/channel toggle_auto` - Toggle auto-responses per channel

### Changed
- Harry now disabled by default in all channels
- Must explicitly enable channels with `/channel enable`

## [1.11.0] - 2026-01-09

### Added

- **Auto Response Toggle**
  - Toggle automatic jump-in responses (team banter)
  - Harry's cockney personality and Oregon hate are ALWAYS ON
  - Only controls "Fuck Oregon!" style auto-responses
  - Oregon player lookup snark always shows (part of personality)

### Changed
- Removed separate cockney/rivalry toggles
- Single "Auto Responses" toggle in dashboard
- Harry is always a cockney asshole Duck-hater 🦆

## [1.10.0] - 2026-01-08

### Added

- **Smart Player Suggestions**
  - "Did you mean?" suggestions for players not found
  - FCS school detection - warns about limited data
  - Automatic retry without team filter if search fails
  - Shows similar players from last name / first name searches
  - Helpful reasons explaining why a player wasn't found

- **FCS Coverage**
  - Added FCS conference and school database
  - Detects Mercer, ETSU, and other FCS schools
  - Warns users about limited CFBD data coverage

## [1.9.1] - 2026-01-08

### Fixed
- Fixed "can only concatenate str to str" error in bulk player lookup
- API stat values now properly converted to integers
- Defensive stat calculations work correctly

## [1.9.0] - 2026-01-08

### Added

- **Web Dashboard**
  - Full web dashboard for managing Harry!
  - Login with Discord OAuth
  - Visual toggle for modules (CFB Data, League)
  - Manage bot admins with clicks
  - Beautiful dark theme UI
  - Server selector for multi-server management

### Technical
- FastAPI backend with async support
- Discord OAuth2 integration
- Session-based authentication
- RESTful API for config management

## [1.8.1] - 2026-01-08

### Added

- **Bulk Player Lookup**
  - Look up multiple players at once!
  - `/players` command for slash interface
  - Natural language: just paste a list to @Harry
  - Supports various formats: Name (Team Pos), Name from Team, etc.
  - Parallel lookups for speed (up to 15 players)
  - Compact display with key stats and recruiting info

## [1.8.0] - 2026-01-08

### Added

- **Per-Server Feature Configuration**
  - `/config` - Enable/disable features per server
  - Modules: Core (always on), CFB Data, League
  - Settings persist across bot restarts
  - Admins can customize Harry for their server

## [1.7.0] - 2026-01-08

### Added

- **Full CFB Data Suite**
  - `/rankings` - AP, Coaches, CFP rankings
  - `/matchup` - All-time series history
  - `/cfb_schedule` - Team schedules and results
  - `/draft_picks` - NFL draft picks by school
  - `/transfers` - Transfer portal activity
  - `/betting` - Spreads and over/unders
  - `/team_ratings` - SP+, SRS, Elo ratings
  - All features work with natural @Harry questions!

## [1.6.1] - 2026-01-08

### Added

- **Official CFBD Library**
  - Refactored to use official `cfbd` Python library
  - More reliable API calls with proper error handling
  - Better type safety and cleaner code

- **Transfer Portal Display**
  - Shows transfer info for portal players
  - Origin → destination team
  - Eligibility status

- **Enhanced Recruiting**
  - National ranking, position rank, state rank
  - Full recruiting class data
  - Searches multiple years automatically

## [1.6.0] - 2026-01-08

### Added

- **Player Lookup**
  - `/player` command to look up any CFB player
  - Get vitals: position, height, weight, year, hometown
  - View season stats: tackles, TFL, sacks, yards, TDs
  - See recruiting info: star rating, national ranking
  - Natural language: "@Harry what do you know about X from Alabama?"

## [1.5.1] - 2026-01-02

### Added

- **Schedule Display**
  - Matchups now show on `/advance` and @everyone advanced
  - User teams are **bolded** in all schedule outputs
  - AI responses format schedules as clean lists

- **Admin Notifications**
  - Timer restore message shows version info
  - Quick preview of latest changes on restart

## [1.5.0] - 2025-12-31

### Added

- **Charter Persistence**
  - Charter now saves to Discord - survives deployments!
  - Automatic sync on any charter update
  - `/sync_charter` command to manually push
  - Charter stored in bot owner's DM

- **Discord Poll Support**
  - `/scan_rules` now detects Discord polls!
  - Extracts poll questions and vote counts
  - Shows winning answer for closed polls

## [1.4.0] - 2025-12-31

### Added

- **Server-Wide Timer Notifications**
  - Timer notifications always go to #general
  - One timer for the whole server
  - `/set_timer_channel` to change notification channel

- **Ephemeral Admin Messages**
  - Admin confirmations now only visible to the admin

## [1.3.0] - 2025-12-31

### Added

- **Interactive Charter Updates**
  - Update charter by talking to Harry naturally
  - Before/after preview with ✅/❌ confirmation
  - Automatic backup before any change
  - `/charter_history` command

- **Rule Scanning**
  - `/scan_rules` to find rule changes in voting channels
  - AI identifies passed/failed/proposed rules
  - Apply all passed rules with one click

- **Co-Commissioner Picker**
  - `/pick_commish` for AI-powered recommendations
  - 🚨 ASSHOLE DETECTOR - rates toxic behavior!
  - Scores: Activity, Helpfulness, Leadership, Drama, Vibes

- **League Staff Tracking**
  - `/league_staff` - View current owner and co-commissioner
  - `/set_league_owner` and `/set_co_commish`

## [1.2.0] - 2025-12-29

### Added

- **Dynasty Week System**
  - Full 30-week CFB 26 dynasty season structure
  - Regular Season, Post-Season, Offseason phases
  - `/week` and `/weeks` commands
  - Week actions and notes

## [1.1.1] - 2025-11-04

### Added

- **Timer Persistence**
  - Timer state persists across deployments via Discord messages
  - Automatic restoration on bot restart

### Fixed
- Guild-specific command sync for instant updates
- Timezone compatibility issues

## [1.1.0] - 2025-11-04

### Added

- **Advance Timer**
  - Custom countdown timers (1-336 hours)
  - Automatic reminders at 24h, 12h, 6h, 1h
  - Progress bar with color-coded urgency

- **Channel Summarization**
  - AI-powered channel message summaries
  - Customizable time periods and focus

- **Charter Management**
  - Direct charter editing from Discord
  - Automatic backups

- **Bot Admin System**
  - Manage bot admins via Discord
  - Discord Administrators have automatic access

## [1.0.0] - 2024-09-17

### Added

- **Core Bot Functionality**
  - Discord.py integration with slash commands
  - AI-powered responses using OpenAI GPT-3.5-turbo
  - Google Docs integration for charter content
  - Comprehensive logging system

- **Slash Commands**
  - `/harry`, `/ask`, `/rule`, `/recruiting`, `/dynasty`, `/charter`, `/help_cfb`

- **Chat Interactions**
  - Natural language processing
  - Rivalry responses (Oregon sucks! 🦆💩)
  - Emoji reactions

---

## Legend

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
