# New Harry Features 🏈

This document outlines the major features added to Harry, the CFB 26 League Bot in version 1.1.0.

**Current Version:** 1.1.0
**Release Date:** November 4, 2025
**Status:** ✅ Production Ready

## 1. ⏰ Advance Timer / Timekeeper

Harry can now manage 48-hour advance countdowns for your league!

### Commands:
- **`/advance`** - Starts a 48-hour countdown timer
  - Announces when started
  - Sends automatic reminders at:
    - 24 hours remaining
    - 12 hours remaining
    - 6 hours remaining
    - 1 hour remaining
  - Announces "TIME'S UP! LET'S ADVANCE!" when countdown finishes

- **`/time_status`** - Check the current countdown status
  - Shows time remaining
  - Displays start and end times
  - Includes a visual progress bar
  - Color-coded urgency levels

- **`/stop_countdown`** (Admin only) - Stops the current countdown

### How It Works:
- Each channel can have its own independent countdown timer
- Timers run in the background and persist during bot restarts (note: requires implementation of persistence)
- Automatic notifications keep everyone informed
- Visual progress tracking with colors:
  - 🟢 Green: 24+ hours remaining (plenty of time!)
  - 🟠 Orange: 12-24 hours (getting closer!)
  - 🟠 Dark Orange: 6-12 hours (time's ticking!)
  - 🔴 Red: 1-6 hours (almost up!)
  - 🔴 Bright Red: <1 hour (LAST HOUR!)

## 2. 📊 Channel Summarization

Harry can now read and summarize channel activity!

### Commands:
- **`/summarize [hours] [focus]`** - Summarize channel messages
  - `hours` (optional, default: 24): How many hours to look back (1-168 max)
  - `focus` (optional): Specific topic to focus on

### Examples:
```
/summarize
/summarize 48
/summarize 24 recruiting
/summarize 72 penalties
```

### Features:
- **AI-Powered Summaries**: Uses OpenAI/Anthropic to generate intelligent summaries
- **Structured Output**: Includes:
  - Main topics discussed
  - Decisions and actions taken
  - Key participants
  - Notable moments
- **Fallback Mode**: If AI is unavailable, provides basic statistics:
  - Message counts
  - Top contributors
  - Activity timeline
- **Smart Filtering**: Ignores bot messages (except important ones)
- **Context-Aware**: Can focus on specific topics

### Use Cases:
- Catch up on missed discussions
- Review league decisions
- Track rule discussions
- Monitor channel activity
- Generate meeting minutes

## 3. 📝 Charter Editing & Management

Harry can now edit the league charter directly from Discord!

### Commands:

#### `/add_rule <title> <content> [position]`
Adds a new rule section to the charter
- **section_title**: Title of the new section
- **rule_content**: Content of the rule
- **position** (optional): Where to add it (default: "end")
  - "end" - Add to the end
  - "after:X.X" - Add after section X.X
  - "before:X.X" - Add before section X.X

**Example:**
```
/add_rule "Playoff Format" "The league uses a 4-team playoff format with top seeds getting home field advantage" end
```

#### `/update_rule <section_identifier> <new_content>`
Updates an existing rule section
- **section_identifier**: Section number or title (e.g., "1.1", "Scheduling")
- **new_content**: New content for the section

**Example:**
```
/update_rule "1.2" "All games must be played by Tuesday and Friday at 9am EST. No exceptions unless approved by commissioner."
```

#### `/view_charter_backups`
Lists all available charter backups
- Shows up to 10 most recent backups
- Displays timestamp and file size
- Admin only

#### `/restore_charter_backup <backup_filename>`
Restores charter from a backup file
- Automatically creates a backup before restoring
- Admin only

### Features:

**AI-Assisted Formatting**:
- Rules are automatically formatted into proper charter style
- Maintains consistent formatting
- Ensures clarity and professionalism

**Automatic Backups**:
- Every edit creates a timestamped backup
- Backups stored in `data/charter_backups/`
- Easy restoration if needed
- Format: `charter_backup_YYYYMMDD_HHMMSS.txt`

**Version Control**:
- Full history of charter changes
- Restore any previous version
- Track when changes were made

**Safety Features**:
- Admin-only access for editing
- Automatic backups before changes
- Validation to prevent corruption
- Confirmation embeds show what changed

### Use Cases:
- Add new rules after league votes
- Update existing rules when policies change
- Document rule changes from channel discussions
- Maintain charter based on league meetings
- Quickly revert bad changes

## 4. 🔐 Bot Admin System

Manage bot administrators directly through Discord!

### Commands:

#### `/add_bot_admin @user`
Add a Discord user as a bot admin
- User gains access to all admin-only commands
- Requires current user to be an admin

**Example:**
```
/add_bot_admin @Commissioner
```

#### `/remove_bot_admin @user`
Remove a user's bot admin privileges
- Revokes admin command access
- Requires current user to be an admin

**Example:**
```
/remove_bot_admin @FormerCommish
```

#### `/list_bot_admins`
View all current bot admins
- Shows display names and user IDs
- Anyone can use this command
- Also shows that Discord Administrators have access

### How It Works:

**Two Ways to Be a Bot Admin:**
1. **Discord Administrator Permission** - Automatic bot admin access
2. **Bot Admin List** - Added via `/add_bot_admin` command

**Admin-Only Commands:**
- `/stop_countdown` - Stop advance timer
- `/add_rule` - Add charter rules
- `/update_rule` - Update charter rules
- `/view_charter_backups` - View backups
- `/restore_charter_backup` - Restore backups
- `/add_bot_admin` - Add new admins
- `/remove_bot_admin` - Remove admins

### Configuration Options:

**Option 1: Through Discord (Recommended)**
Use `/add_bot_admin @user` in Discord once deployed

**Option 2: Environment Variable**
Set `BOT_ADMIN_IDS` in your `.env` file:
```
BOT_ADMIN_IDS=123456789012345678,987654321098765432
```
(Comma-separated list of Discord User IDs)

**Option 3: Hardcoded**
Edit `src/cfb_bot/utils/admin_check.py` and add User IDs to `HARDCODED_ADMINS` list

## 5. 📜 Version Control & Changelog

Track bot versions and view update history!

### Commands:

#### `/version`
Shows current bot version information
- Version number (e.g., v1.1.0)
- Release date
- Total versions available

**Example Output:**
```
🏈 Harry v1.1.0
🎉 Major Feature Update
📅 Release Date: 2025-11-04
📊 Total Versions: 2
```

#### `/changelog [version]`
View version changelog and update history

**Without version parameter:**
```
/changelog
```
Shows summary of all versions

**With specific version:**
```
/changelog 1.1.0
```
Shows detailed changes for that version

#### `/whats_new`
Showcase latest features in a user-friendly format
- Highlights new features with examples
- Perfect for announcing updates to your league
- Automatically shows current version

### Features:

**Complete Version History:**
- All versions tracked in `version_manager.py`
- Organized by release date
- Categorized features by type
- Emoji indicators for each category

**Easy Updates:**
When adding new features:
1. Update `CURRENT_VERSION` in `version_manager.py`
2. Add new entry to `CHANGELOG` dict
3. Categorize features appropriately
4. Commit and deploy!

**Version Display:**
- Bot startup shows version in logs
- `/whats_new` shows current version
- Help commands reference version
- Easy to track what's running

## Technical Details

### File Structure:
```
src/cfb_bot/
├── utils/
│   ├── timekeeper.py      # Advance timer functionality
│   ├── summarizer.py      # Channel summarization
│   ├── charter_editor.py  # Charter management
│   ├── admin_check.py     # Bot admin management
│   └── version_manager.py # Version control & changelog
└── bot.py                 # Main bot with new commands
```

### Dependencies:
All features use existing dependencies:
- `discord.py` - Discord API
- `asyncio` - Async operations
- OpenAI/Anthropic (optional) - AI summaries and formatting
- Python standard library (datetime, os, json, logging)

### Integration:
- All features are fully integrated into the main bot
- Graceful fallbacks if AI is unavailable
- Comprehensive error handling
- Full logging for debugging
- Cockney personality maintained throughout!

## Future Enhancements (Potential)

### Timekeeper:
- Persistent timers (survive bot restarts)
- Custom countdown durations
- Multiple simultaneous timers per channel
- Scheduled automatic advances
- Integration with Google Calendar

### Summarization:
- Export summaries to files
- Email summaries to league members
- Compare summaries across time periods
- Trend analysis (most discussed topics over time)
- Sentiment analysis

### Charter Editing:
- GitHub integration for version control
- Diff view for changes
- Approval workflow (propose → vote → implement)
- Auto-sync with Google Docs
- Rule change notifications
- Markdown export

## Notes

- All admin commands require Discord Administrator permissions OR bot admin status
- Charter backups are created automatically before any edits
- Summaries work best with AI enabled (OpenAI or Anthropic)
- Timers are per-channel and independent
- All features include Harry's signature cockney personality!
- Version history is tracked in `src/cfb_bot/utils/version_manager.py`

## ⚠️ IMPORTANT: Updating Versions

**When adding new features, you MUST update the version!**

See `docs/VERSION_MANAGEMENT.md` for complete instructions on:
- How to increment version numbers
- How to add changelog entries
- Version numbering conventions
- Release process

**Quick Reminder:**
1. Edit `src/cfb_bot/utils/version_manager.py`
2. Update `CURRENT_VERSION` (e.g., "1.1.0" → "1.2.0")
3. Add new entry to `CHANGELOG` dict with all changes
4. Commit with descriptive message
5. Push and deploy!

---

**Implemented**: November 4, 2025
**Version**: 1.1.0
**Author**: Harry (with assistance from Craig's AI assistant, innit!)
**Last Updated**: November 4, 2025
