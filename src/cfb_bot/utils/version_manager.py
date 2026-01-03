#!/usr/bin/env python3
"""
Version Manager for CFB 26 League Bot
Tracks versions and changelog
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger('CFB26Bot.Version')

# Current version
CURRENT_VERSION = "1.5.1"

# Changelog - organized by version
CHANGELOG: Dict[str, Dict] = {
    "1.5.1": {
        "date": "2026-01-02",
        "title": "Schedule Display & Admin Notifications",
        "emoji": "📅",
        "features": [
            {
                "category": "Schedule Display",
                "emoji": "🏈",
                "changes": [
                    "Matchups now show on /advance and @everyone advanced",
                    "User teams are **bolded** in all schedule outputs",
                    "AI responses format schedules as clean lists",
                    "Bye teams included in advance announcements"
                ]
            },
            {
                "category": "Admin Notifications",
                "emoji": "🔔",
                "changes": [
                    "Timer restore message shows version info",
                    "Quick preview of latest changes on restart",
                    "Helps admins see what changed after deploy"
                ]
            }
        ]
    },
    "1.5.0": {
        "date": "2025-12-31",
        "title": "Discord Charter Persistence & Poll Support",
        "emoji": "📜",
        "features": [
            {
                "category": "Charter Persistence",
                "emoji": "💾",
                "changes": [
                    "Charter now saves to Discord - survives deployments!",
                    "Automatic sync on any charter update",
                    "/sync_charter command to manually push to Discord",
                    "Falls back to file if no Discord version exists",
                    "Charter stored in bot owner's DM (invisible to users)"
                ]
            },
            {
                "category": "Discord Poll Support",
                "emoji": "🗳️",
                "changes": [
                    "/scan_rules now detects Discord polls!",
                    "Extracts poll questions and vote counts",
                    "Shows winning answer for closed polls",
                    "Analyzes both text messages and polls"
                ]
            },
            {
                "category": "Pick Commish Improvements",
                "emoji": "👑",
                "changes": [
                    "Added channel selection: /pick_commish #channel",
                    "DO NOT PICK and BIGGEST ASSHOLE are now separate",
                    "Asshole score based on actual toxic behavior, not ranking"
                ]
            }
        ]
    },
    "1.4.1": {
        "date": "2025-12-31",
        "title": "Code Quality & Settings Persistence",
        "emoji": "🔧",
        "features": [
            {
                "category": "Bug Fixes",
                "emoji": "🐛",
                "changes": [
                    "Fixed all bare 'except:' blocks with specific exception types",
                    "Notification channel now persists across bot restarts",
                    "/set_timer_channel setting is saved to Discord"
                ]
            },
            {
                "category": "Code Quality",
                "emoji": "🔧",
                "changes": [
                    "Added get_notification_channel() helper for consistent channel lookup",
                    "Refactored exception handling for better error tracking",
                    "Updated README with v1.4.0 features"
                ]
            }
        ]
    },
    "1.4.0": {
        "date": "2025-12-31",
        "title": "Server-Wide Timer & Ephemeral Messages",
        "emoji": "📢",
        "features": [
            {
                "category": "Server-Wide Timer Notifications",
                "emoji": "📢",
                "changes": [
                    "Timer notifications now always go to #general",
                    "One timer for the whole server (not per-channel)",
                    "Includes: Advance start, 24h/12h/6h/1h warnings, TIME'S UP",
                    "/set_timer_channel to change notification channel",
                    "Schedule announcements also go to timer channel"
                ]
            },
            {
                "category": "Ephemeral Admin Messages",
                "emoji": "👁️",
                "changes": [
                    "Admin confirmations now only visible to the admin",
                    "/stop_countdown success → ephemeral",
                    "/set_season_week success → ephemeral",
                    "/set_league_owner success → ephemeral",
                    "/set_co_commish success → ephemeral",
                    "/advance confirmation → ephemeral (announcement goes to #general)",
                    "Timer Restored → goes to admin channel only"
                ]
            }
        ]
    },
    "1.3.0": {
        "date": "2025-12-31",
        "title": "Interactive Charter & Co-Commish Picker",
        "emoji": "👑",
        "features": [
            {
                "category": "Interactive Charter Updates",
                "emoji": "📝",
                "changes": [
                    "Update charter by talking to Harry naturally!",
                    "Example: '@Harry update the advance time to 10am'",
                    "Example: '@Harry add a rule: no trading during playoffs'",
                    "Before/after preview with ✅/❌ confirmation",
                    "Automatic backup before any change",
                    "Changelog tracks who changed what and when",
                    "/charter_history command to view recent changes"
                ]
            },
            {
                "category": "Rule Scanning",
                "emoji": "🔍",
                "changes": [
                    "/scan_rules command to find rule changes in voting channels",
                    "Natural language: '@Harry scan #voting for rule changes'",
                    "AI identifies passed/failed/proposed rules",
                    "Shows vote counts when available",
                    "React with 📝 to generate charter updates",
                    "Apply all passed rules to charter with one click"
                ]
            },
            {
                "category": "Co-Commissioner Picker",
                "emoji": "👑",
                "changes": [
                    "/pick_commish command for AI-powered recommendations",
                    "Analyzes chat activity and participation",
                    "🚨 ASSHOLE DETECTOR - rates toxic behavior!",
                    "Scores: Activity, Helpfulness, Leadership, Drama, Vibes",
                    "Ranks ALL participants with personalized roasts",
                    "Calls out biggest asshole who should NEVER be commish"
                ]
            },
            {
                "category": "League Staff Tracking",
                "emoji": "👔",
                "changes": [
                    "/league_staff - View current owner and co-commissioner",
                    "/set_league_owner - Set the league owner",
                    "/set_co_commish - Set the co-commissioner",
                    "Special option: 'We don't fucking have one' for co-commish",
                    "Persists across bot restarts"
                ]
            },
            {
                "category": "Code Quality",
                "emoji": "🔧",
                "changes": [
                    "Fixed all bare 'except:' blocks with specific exceptions",
                    "Added cleanup task for expired pending requests",
                    "Memory leak prevention for processed messages",
                    "Python 3.13 compatibility improvements"
                ]
            }
        ]
    },
    "1.2.0": {
        "date": "2025-12-29",
        "title": "CFB 26 Dynasty Week System",
        "emoji": "🏈",
        "features": [
            {
                "category": "Dynasty Week Counter",
                "emoji": "📅",
                "changes": [
                    "Added full CFB 26 Dynasty season week structure (30 weeks total)",
                    "Regular Season: Week 0 (Season Kickoff) through Week 15",
                    "Post-Season: Conference Championships, Bowl Weeks 1-4, End of Season Recap",
                    "Offseason: Portal Weeks 1-4, National Signing Day, Training Results",
                    "Offseason: Encourage Transfers, Preseason",
                    "Season phase tracking (Regular Season, Post-Season, Offseason)"
                ]
            },
            {
                "category": "Week Actions & Notes",
                "emoji": "📋",
                "changes": [
                    "Each week now shows available actions (staff moves, job offers, etc.)",
                    "Important notes displayed (last chance reminders, deadlines)",
                    "Bowl weeks show hiring/firing windows",
                    "Offseason weeks show portal and recruiting actions",
                    "/time_status shows upcoming week actions"
                ]
            },
            {
                "category": "Improved Display",
                "emoji": "✨",
                "changes": [
                    "Week transitions now show proper CFB 26 week names",
                    "Season phase displayed alongside week info",
                    "/time_status shows current and next week with actions",
                    "/set_season_week shows proper week name, phase, and actions",
                    "Times Up message displays phase and week progression"
                ]
            }
        ]
    },
    "1.1.1": {
        "date": "2025-11-04",
        "title": "Bug Fixes & Improvements",
        "emoji": "🐛",
        "features": [
            {
                "category": "Bug Fixes",
                "emoji": "🐛",
                "changes": [
                    "Fixed summarizer timezone compatibility issue (discord.utils.utc → timezone.utc)",
                    "Channel summarization now works with all discord.py versions",
                    "Guild-specific command sync for instant updates (5 seconds vs 1 hour)",
                    "Commands now appear immediately in configured servers"
                ]
            },
            {
                "category": "Security & Permissions",
                "emoji": "🔐",
                "changes": [
                    "Advance timer commands now require admin permissions",
                    "/advance restricted to admins only",
                    "/stop_countdown now uses bot admin system",
                    "Added hardcoded admin support for permanent admins",
                    "Both Discord Administrators and Bot Admins can manage timers"
                ]
            },
            {
                "category": "Configuration",
                "emoji": "⚙️",
                "changes": [
                    "Added support for multiple guild instant sync",
                    "Configured two servers for instant command updates",
                    "Improved admin permission checking across all commands"
                ]
            },
            {
                "category": "Documentation",
                "emoji": "📖",
                "changes": [
                    "Updated help command with admin-only labels",
                    "Clarified which commands require admin access",
                    "Updated README with permission requirements"
                ]
            }
        ]
    },
    "1.1.0": {
        "date": "2025-11-04",
        "title": "Major Feature Update",
        "emoji": "🎉",
        "features": [
            {
                "category": "Advance Timer",
                "emoji": "⏰",
                "changes": [
                    "Added 48-hour countdown timer with custom duration support",
                    "Automatic notifications at 24h, 12h, 6h, and 1h remaining",
                    "'TIME'S UP! LET'S ADVANCE!' announcement when countdown ends",
                    "Progress bar with color-coded urgency levels",
                    "Commands: `/advance [hours]`, `/time_status`, `/stop_countdown`"
                ]
            },
            {
                "category": "Channel Summarization",
                "emoji": "📊",
                "changes": [
                    "AI-powered channel message summarization",
                    "Customizable time periods (1-168 hours)",
                    "Optional focus on specific topics",
                    "Shows main topics, decisions, participants, and notable moments",
                    "Fallback to basic stats when AI unavailable",
                    "Command: `/summarize [hours] [focus]`"
                ]
            },
            {
                "category": "Charter Management",
                "emoji": "📝",
                "changes": [
                    "Direct charter editing from Discord",
                    "Add new rules with AI-assisted formatting",
                    "Update existing rule sections",
                    "Automatic backups before every change",
                    "View and restore from backup history",
                    "Commands: `/add_rule`, `/update_rule`, `/view_charter_backups`, `/restore_charter_backup`"
                ]
            },
            {
                "category": "Bot Admin System",
                "emoji": "🔐",
                "changes": [
                    "Manage bot admins directly through Discord",
                    "Add/remove users as bot admins",
                    "List all current bot admins",
                    "Discord Administrators have automatic bot admin access",
                    "Commands: `/add_bot_admin`, `/remove_bot_admin`, `/list_bot_admins`"
                ]
            },
            {
                "category": "Other Improvements",
                "emoji": "✨",
                "changes": [
                    "Added `/whats_new` command to showcase latest features",
                    "Added `/changelog` command for version history",
                    "Better error handling across all features",
                    "Improved logging for debugging",
                    "Maintained cockney personality throughout!"
                ]
            }
        ]
    },
    "1.0.0": {
        "date": "2025-10-15",
        "title": "Initial Release",
        "emoji": "🚀",
        "features": [
            {
                "category": "Core Features",
                "emoji": "🏈",
                "changes": [
                    "AI-powered responses about league rules",
                    "League charter access and search",
                    "Team information lookup",
                    "Rivalry responses and fun interactions",
                    "Slash commands for easy interaction",
                    "Smart filtering for league-related questions"
                ]
            },
            {
                "category": "AI Integration",
                "emoji": "🤖",
                "changes": [
                    "OpenAI GPT-3.5 integration",
                    "Anthropic Claude support",
                    "Context-aware responses",
                    "Token usage tracking",
                    "Sarcastic personality (Harry's trademark!)"
                ]
            },
            {
                "category": "Commands",
                "emoji": "⚡",
                "changes": [
                    "/harry - Ask questions conversationally",
                    "/ask - AI-powered rule answers",
                    "/charter - Link to official charter",
                    "/rules - League rules information",
                    "/search - Search charter content",
                    "/tokens - View AI usage statistics"
                ]
            }
        ]
    }
}

class VersionManager:
    """Manages version information and changelog"""

    def __init__(self):
        self.current_version = CURRENT_VERSION
        self.changelog = CHANGELOG

    def get_current_version(self) -> str:
        """Get the current version string"""
        return self.current_version

    def get_version_info(self, version: str) -> Optional[Dict]:
        """Get information about a specific version"""
        return self.changelog.get(version)

    def get_all_versions(self) -> List[str]:
        """Get list of all versions"""
        return sorted(self.changelog.keys(), reverse=True)

    def get_latest_version_info(self) -> Dict:
        """Get information about the latest version"""
        return self.changelog.get(self.current_version, {})

    def format_version_embed_data(self, version: str) -> Optional[Dict]:
        """
        Format version data for Discord embed

        Returns:
            Dict with title, description, and fields for embed
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return None

        embed_data = {
            "title": f"{version_info['emoji']} Version {version} - {version_info['title']}",
            "description": f"Released: {version_info['date']}",
            "fields": []
        }

        for feature_group in version_info.get('features', []):
            category = feature_group.get('category', 'Features')
            emoji = feature_group.get('emoji', '•')
            changes = feature_group.get('changes', [])

            # Format changes as bullet points
            changes_text = '\n'.join([f"• {change}" for change in changes])

            embed_data["fields"].append({
                "name": f"{emoji} {category}",
                "value": changes_text,
                "inline": False
            })

        return embed_data

    def get_version_summary(self) -> str:
        """Get a summary of all versions"""
        versions = self.get_all_versions()
        summary_lines = []

        for version in versions:
            info = self.changelog.get(version, {})
            emoji = info.get('emoji', '📌')
            title = info.get('title', 'Update')
            date = info.get('date', 'Unknown')
            summary_lines.append(f"{emoji} **v{version}** - {title} ({date})")

        return '\n'.join(summary_lines)

    def compare_versions(self, from_version: str, to_version: str) -> List[str]:
        """
        Get all changes between two versions

        Returns:
            List of change descriptions
        """
        all_versions = self.get_all_versions()

        try:
            from_idx = all_versions.index(from_version)
            to_idx = all_versions.index(to_version)

            # Get versions between (inclusive)
            if from_idx > to_idx:
                from_idx, to_idx = to_idx, from_idx

            versions_between = all_versions[to_idx:from_idx+1]

            all_changes = []
            for version in versions_between:
                version_info = self.changelog.get(version, {})
                for feature_group in version_info.get('features', []):
                    changes = feature_group.get('changes', [])
                    all_changes.extend(changes)

            return all_changes

        except ValueError:
            return []
