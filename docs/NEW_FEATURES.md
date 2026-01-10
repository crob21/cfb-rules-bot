# Harry's Features 🏈

This document outlines all features of Harry, the CFB 26 League Bot.

**Current Version:** 1.17.5
**Last Updated:** January 10, 2026
**Status:** ✅ Production Ready

---

## ⭐ Recruiting Module

Look up recruit profiles with rankings, offers, predictions, visits, and photos!

> **Data Sources:** On3/Rivals (default) or 247Sports Composite. Switch with `/recruit_source`

### Single Recruit Lookup

**Command:** `/recruit <name> [year]`

**Natural Language:** `@Harry recruit Arch Manning`

**Shows:**
- Player photo (thumbnail in embed)
- ⭐ Star rating and composite rating
- 🏆 National, position, and state rankings
- 📏 Height, weight, hometown, high school
- ✅ Commitment status with signing date
- 🔮 Predictions (top 5 schools with percentages)
- 📋 Offers list (all schools that offered)
- ✈️ Visit history (official/unofficial with dates)
- 🔗 Link to full On3/Rivals profile

### Top Recruits

**Command:** `/top_recruits [position] [state] [year] [top]`

**Examples:**
- `/top_recruits position:QB` - Top QBs nationally
- `/top_recruits state:TX` - Top recruits from Texas
- `/top_recruits top:50` - Top 50 overall

### Recruiting Class Rankings

**Command:** `/recruiting_class <team> [year]`

**Shows:**
- Team's national ranking
- Total commits
- Average rating
- Star breakdown

### Team Rankings

**Command:** `/recruiting_rankings [year] [top]`

**Shows:**
- Top 25 (or custom) team recruiting rankings
- Points, average rating per team

### Data Source Selection

**Command:** `/recruit_source [on3|247]`

| Source | Description |
|--------|-------------|
| **On3/Rivals** | Default. Server-side rendered, fast & reliable. Includes predictions, offers, visits. |
| **247Sports** | Legacy. Deep search option for ~3000 recruits. |

---

## 🏈 CFB Data Module

Access comprehensive college football data powered by CollegeFootballData.com API.

> **Note:** All CFB Data commands automatically default to the current season and week. No need to specify year/week unless you want historical data!

### Player Lookup

**Commands:**
- `/player <name> [team]` - Look up a single player
- `/players <list>` - Bulk lookup (up to 15 players)

**Natural Language:**
- `@Harry what do you know about Jalen Milroe from Alabama?`
- `@Harry stats for Caleb Williams USC`
- Just paste a list of players and Harry will look them all up!

**Features:**
- Player vitals (height, weight, position, year, hometown)
- Season stats (rushing, passing, receiving, defense)
- Recruiting info (stars, national rank, position rank)
- Transfer portal status
- Smart suggestions for players not found
- FCS school detection with limited-data warnings

### Rankings

**Command:** `/rankings [poll]`

**Natural Language:** `@Harry where is Ohio State ranked?`

**Supported Polls:**
- AP Top 25
- Coaches Poll
- College Football Playoff

### Matchup History

**Command:** `/matchup <team1> <team2>`

**Natural Language:** `@Harry Alabama vs Auburn all-time record`

**Shows:**
- All-time series record
- Recent game results
- Home/away splits

### Team Schedules

**Command:** `/cfb_schedule <team> [year]`

**Natural Language:** `@Harry when does Nebraska play next?`

**Shows:**
- Full season schedule
- Game results (W/L, scores)
- Upcoming opponents
- Bye weeks

### NFL Draft

**Command:** `/draft_picks <team> [year]`

**Natural Language:** `@Harry who got drafted from Georgia?`

**Shows:**
- Draft picks by school
- Round, pick number
- Position, NFL team

### Transfer Portal

**Command:** `/transfers <team>`

**Natural Language:** `@Harry USC transfer portal activity`

**Shows:**
- Incoming transfers (with origin school)
- Outgoing transfers (with destination)
- Player ratings

### Betting Lines

**Command:** `/betting [team]` - Shows upcoming games, or filter by team

**Natural Language:** `@Harry who's favored in Bama vs Georgia?`

**Shows:**
- Point spread
- Over/under
- Moneyline (when available)
- Auto-detects postseason/playoff games

### Advanced Ratings

**Command:** `/team_ratings <team>`

**Natural Language:** `@Harry how good is Texas?`

**Shows:**
- SP+ ratings (overall, offense, defense)
- SRS (Simple Rating System)
- Elo rating
- FPI (when available)

---

## 🏫 High School Stats Module

Look up high school football career stats from MaxPreps for recruiting research.

> **Note:** This module uses web scraping and is disabled by default. Enable with `/config enable hs_stats`

### Single Player Lookup

**Command:** `/hs_stats <name> [state] [school]`

**Natural Language:** `@Harry hs stats Gavin Day NV`

**Shows:**
- 🏈 **Player Info:** Name, school, location (city, state)
- 📍 **Position:** QB, WR, RB, DB, LB, etc.
- 📏 **Physical:** Height, weight, class year (Senior/Junior/etc.)
- 📊 **Career Stats:**
  - **Defense:** Solo tackles, total tackles, sacks, interceptions
  - **Rushing:** Carries, yards, avg, TDs, long run
  - **Passing:** Completions, attempts, yards, TDs, INTs
  - **Receiving:** Receptions, yards, avg, TDs
  - **All-Purpose:** Rush/Rec/KR/PR/IR yards, total
- 📅 **Season Breakdown:** Stats by grade level (Sr/Jr/So/Fr)
- 🔗 **Link:** Direct link to MaxPreps profile

**Example Output:**
```
🏈 Gavin Day
🏫 Faith Lutheran (Las Vegas, NV)
📍 DB • 6'3" • 190 lbs • Senior

Sr. 25-26 (14 GP)
  🔄 All Purpose: 165 Total | 165 IR

Jr. 24-25 (12 GP)
  🔄 All Purpose: 71 Total | 71 IR

📊 Career Totals
  🛡️ Defense: 210 Solo/283 TKL
```

### Bulk Lookup

**Command:** `/hs_stats_bulk <player_list>`

Look up multiple high school players at once for recruiting boards.

**Format:**
```
Player Name, State
Player Name 2, State
Player Name 3
```

---

## ⏰ Advance Timer / Timekeeper

Server-wide countdown timers for league advances.

### Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/advance [hours]` | Start countdown (default 48h) | Admin |
| `/time_status` | Check countdown progress | Everyone |
| `/stop_countdown` | Stop the timer | Admin |
| `/set_timer_channel #channel` | Set notification channel | Admin |

### Features

- **Custom Duration**: 1-336 hours (default 48h)
- **Automatic Notifications**: 24h, 12h, 6h, 1h remaining
- **Visual Progress Bar**: Color-coded urgency levels
- **Server-Wide**: One timer for the whole Discord
- **Persistence**: Survives bot restarts and deployments!
- **Centralized Notifications**: All alerts go to one channel (#general by default)

### Progress Bar Colors

| Time Remaining | Color |
|----------------|-------|
| 24+ hours | 🟢 Green |
| 12-24 hours | 🟠 Orange |
| 6-12 hours | 🟠 Dark Orange |
| 1-6 hours | 🔴 Red |
| < 1 hour | 🔴 Bright Red |

---

## 📅 Dynasty Week System

Full 30-week CFB 26 season tracking with actions and notes.

### Commands

| Command | Description |
|---------|-------------|
| `/week` | Show current week, phase, and actions |
| `/weeks` | Show full 30-week dynasty schedule |
| `/set_season_week <season> <week>` | Set current season and week (Admin) |

### Season Structure

**Regular Season (Weeks 0-15)**
- Week 0: Season Kickoff
- Weeks 1-12: Regular Season
- Week 13: Rivalry Week
- Week 14-15: Conference Championships

**Post-Season (Weeks 16-21)**
- Weeks 16-19: Bowl Games / Playoffs
- Week 20: End of Season Recap
- Week 21: Award Show

**Offseason (Weeks 22-29)**
- Weeks 22-25: Transfer Portal
- Week 26: National Signing Day
- Week 27: Training Results
- Week 28: Encourage Transfers
- Week 29: Preseason → New Season!

---

## 📝 Charter Management

Interactive charter editing and rule scanning.

### Interactive Updates

Talk to Harry naturally:
```
@Harry update the advance time to 10am EST
@Harry add a rule: no trading during playoffs
@Harry change quarter length to 5 minutes
```

**Features:**
- Before/after preview
- ✅/❌ confirmation buttons
- Automatic backups
- Changelog tracking

### Rule Scanning

**Command:** `/scan_rules #channel [hours]`

**Natural Language:** `@Harry scan #voting for rule changes`

**Features:**
- Detects passed, failed, and proposed rules
- Extracts vote counts from Discord polls
- Apply all passed rules with one click
- AI-powered rule identification

### Charter History

**Command:** `/charter_history`

View recent charter changes with who changed what and when.

---

## 👑 Co-Commissioner Picker

AI-powered co-commissioner recommendations.

**Command:** `/pick_commish [hours] [#channel]`

### The Asshole Detector 🚨

Harry rates candidates on:
- **Activity Level** - How often they participate
- **Helpfulness** - Do they help others?
- **Leadership** - Natural leader vibes?
- **Asshole Score** - Are they a dick?
- **Drama Score** - Stir up trouble?
- **Vibes/Humor** - Fun to be around?
- **Reliability** - Follow through?
- **Knowledge** - Know the game?

Includes personalized roasts for each candidate!

---

## ⚙️ Configuration System

### Per-Server Modules

**Command:** `/config [module]`

| Module | Description | Default |
|--------|-------------|---------|
| **Core** | Harry's personality, AI chat | Always On |
| **CFB Data** | Player lookup, rankings, etc. | Enabled |
| **Recruiting** | Recruit lookup (On3/247Sports) | Enabled |
| **League** | Timer, charter, dynasty | Disabled |
| **HS Stats** | High school stats (MaxPreps) | Disabled |

### Per-Channel Controls

**Command:** `/channel <action>`

| Action | Description |
|--------|-------------|
| `view` | See current channel settings |
| `enable` | Enable Harry in this channel |
| `disable` | Disable Harry in this channel |
| `disable_all` | Clear whitelist for server |
| `toggle_rivalry` | Toggle rivalry auto-responses |

**Important:** Harry is disabled by default! Use `/channel enable` to activate.

### Web Dashboard

Run the dashboard for visual configuration:
```bash
python run_dashboard.py
# Visit http://localhost:8080
```

**Features:**
- Discord OAuth login
- Visual module toggles
- Bot admin management
- Multi-server support

---

## 🔐 Bot Admin System

### Commands

| Command | Description |
|---------|-------------|
| `/add_bot_admin @user` | Add a bot admin |
| `/remove_bot_admin @user` | Remove a bot admin |
| `/list_bot_admins` | View all bot admins |

### Who Can Be Admin?

1. **Discord Administrator** - Automatic access
2. **Bot Admin List** - Added via command
3. **Hardcoded Admins** - Set in env vars

---

## 📦 Storage System

Harry uses a pluggable storage system for scalability.

### Discord DM Storage (Default)
- **Pros**: Free, no setup, survives deploys
- **Cons**: ~10-20 server limit
- **Config**: `STORAGE_BACKEND=discord` (default)

### Supabase Storage (Scaling)
- **Pros**: Unlimited servers, proper backups
- **Cons**: Requires setup
- **Config**: `STORAGE_BACKEND=supabase`

To switch backends, just change the env var and deploy!

---

## 😄 Harry's Personality

Harry's core personality is **always on**:

- 🎩 **Cockney Accent** - "Oi mate, let me tell ya..."
- 😈 **Snarky Asshole** - Roasts and sarcasm included
- 🦆 **Oregon Hater** - Deep, unhinged hatred of the Ducks

### What's Toggleable?

Only **auto-responses** (unprompted jump-ins) can be toggled:
- "Fuck Oregon!" when someone mentions Ducks
- 🦆 emoji reactions triggering responses
- Random Oregon jokes in timer messages

Use `/channel toggle_rivalry` to control these per-channel.

---

## 📊 Channel Summarization

AI-powered discussion summaries.

**Command:** `/summarize [hours] [focus]`

**Natural Language:** `@Harry what happened in the last 3 hours?`

**Features:**
- Main topics discussed
- Decisions and actions
- Key participants
- Notable moments
- Optional focus filter (e.g., "rules", "recruiting")

---

## 📨 Message Relay

Relay messages between users.

**Usage:** `@Harry tell @User to <message>`

**Examples:**
```
@Harry tell @wustyman to fuck off
@Harry tell @boozerob the game is ready
```

---

## Technical Details

### File Structure
```
src/cfb_bot/
├── bot.py                   # Main Discord bot
├── ai/
│   └── ai_integration.py    # OpenAI/Anthropic
└── utils/
    ├── storage.py           # Storage abstraction
    ├── server_config.py     # Per-server config
    ├── cfb_data.py          # CFB data (CFBD API)
    ├── recruiting_scraper.py # 247Sports scraper
    ├── on3_scraper.py       # On3/Rivals scraper
    ├── hs_stats_scraper.py  # High school stats (MaxPreps)
    ├── timekeeper.py        # Timer & weeks
    ├── charter_editor.py    # Charter management
    ├── summarizer.py        # Channel summaries
    └── version_manager.py   # Version tracking
```

### Dependencies
- `discord.py` - Discord API
- `cfbd` - CollegeFootballData.com API
- `openai` / `anthropic` - AI integration
- `fastapi` - Web dashboard
- `aiohttp` - Async HTTP

---

**Author:** Harry (with assistance from Craig's AI assistant, innit!)
**Version:** 1.17.4
**Last Updated:** January 10, 2026
