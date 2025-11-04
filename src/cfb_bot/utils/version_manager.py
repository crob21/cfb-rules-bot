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
CURRENT_VERSION = "1.1.0"

# Changelog - organized by version
CHANGELOG: Dict[str, Dict] = {
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
