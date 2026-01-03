#!/usr/bin/env python3
"""
Schedule Manager for CFB 26 League Bot
Manages and queries the league schedule data
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('CFB26Bot.Schedule')

# Schedule data file location
SCHEDULE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "schedule.json"


class ScheduleManager:
    """Manages league schedule data and queries"""

    def __init__(self):
        self.schedule_data: Dict = {}
        self.season: int = 1
        self.teams: List[str] = []
        self._load_schedule()

    def _load_schedule(self) -> bool:
        """Load schedule data from JSON file"""
        try:
            if SCHEDULE_FILE.exists():
                with open(SCHEDULE_FILE, 'r') as f:
                    self.schedule_data = json.load(f)
                self.season = self.schedule_data.get('season', 1)
                self.teams = self.schedule_data.get('teams', [])
                logger.info(f"✅ Loaded schedule for Season {self.season} ({len(self.teams)} teams)")
                return True
            else:
                logger.warning(f"⚠️ Schedule file not found: {SCHEDULE_FILE}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to load schedule: {e}")
            return False

    def reload_schedule(self) -> bool:
        """Reload schedule data from file"""
        return self._load_schedule()

    def get_week_schedule(self, week: int) -> Optional[Dict]:
        """
        Get the schedule for a specific week.

        Args:
            week: Week number (0-13 for regular season)

        Returns:
            Dict with 'bye_teams' and 'games' lists, or None if not found
        """
        schedule = self.schedule_data.get('schedule', {})
        return schedule.get(str(week))

    def get_team_game(self, team: str, week: int) -> Optional[Dict]:
        """
        Get a specific team's game for a week.

        Args:
            team: Team name (case-insensitive)
            week: Week number

        Returns:
            Dict with game info including 'opponent', 'location' (home/away), or None if bye/not found
        """
        week_data = self.get_week_schedule(week)
        if not week_data:
            return None

        team_lower = team.lower()

        # Check if team has a bye
        bye_teams = [t.lower() for t in week_data.get('bye_teams', [])]
        if team_lower in bye_teams:
            return {'bye': True, 'team': team}

        # Find the game
        for game in week_data.get('games', []):
            if game['home'].lower() == team_lower:
                return {
                    'bye': False,
                    'team': team,
                    'opponent': game['away'],
                    'location': 'home',
                    'matchup': f"{game['away']} at {game['home']}"
                }
            elif game['away'].lower() == team_lower:
                return {
                    'bye': False,
                    'team': team,
                    'opponent': game['home'],
                    'location': 'away',
                    'matchup': f"{game['away']} at {game['home']}"
                }

        return None

    def get_bye_teams(self, week: int) -> List[str]:
        """Get list of teams on bye for a specific week"""
        week_data = self.get_week_schedule(week)
        if not week_data:
            return []
        return week_data.get('bye_teams', [])

    def get_all_games(self, week: int) -> List[Dict]:
        """Get all games for a specific week"""
        week_data = self.get_week_schedule(week)
        if not week_data:
            return []
        return week_data.get('games', [])

    def find_team(self, query: str) -> Optional[str]:
        """
        Find a team by partial name match.

        Args:
            query: Search query (case-insensitive)

        Returns:
            Full team name if found, None otherwise
        """
        query_lower = query.lower()

        # Try exact match first
        for team in self.teams:
            if team.lower() == query_lower:
                return team

        # Try partial match
        for team in self.teams:
            if query_lower in team.lower():
                return team

        # Try matching common abbreviations
        abbreviations = {
            'msu': 'Michigan St',
            'michigan state': 'Michigan St',
            'mich st': 'Michigan St',
            'nd': 'Notre Dame',
            'irish': 'Notre Dame',
            'huskers': 'Nebraska',
            'neb': 'Nebraska',
            'longhorns': 'Texas',
            'ut': 'Texas',
            'tigers': 'LSU',
            'rainbow warriors': 'Hawaii',
            'warriors': 'Hawaii',
        }

        if query_lower in abbreviations:
            return abbreviations[query_lower]

        return None

    def get_team_full_schedule(self, team: str) -> List[Dict]:
        """
        Get a team's full season schedule.

        Args:
            team: Team name

        Returns:
            List of game info for each week
        """
        schedule = []
        for week in range(14):  # Weeks 0-13
            game = self.get_team_game(team, week)
            if game:
                game['week'] = week
                schedule.append(game)
        return schedule

    def format_week_schedule(self, week: int) -> str:
        """
        Format the week's schedule as a readable string.

        Args:
            week: Week number

        Returns:
            Formatted string of the week's schedule
        """
        week_data = self.get_week_schedule(week)
        if not week_data:
            return f"No schedule data for Week {week}"

        lines = [f"**Week {week} Schedule:**\n"]

        # Bye teams
        bye_teams = week_data.get('bye_teams', [])
        if bye_teams:
            lines.append(f"🛋️ **Bye Week:** {', '.join(bye_teams)}\n")

        # Games
        games = week_data.get('games', [])
        if games:
            lines.append("**Games:**")
            for game in games:
                lines.append(f"• {game['away']} at {game['home']}")

        return "\n".join(lines)

    def get_schedule_context_for_ai(self) -> str:
        """
        Generate a context string about the schedule for the AI.

        Returns:
            String containing schedule information for AI context
        """
        context_lines = [
            f"League Schedule Information (Season {self.season}):",
            f"USER-CONTROLLED TEAMS (bold these in responses): {', '.join(self.teams)}",
            "NOTE: When listing matchups, **bold** any team from the user-controlled list above.",
            "",
            "Schedule by week:"
        ]

        schedule = self.schedule_data.get('schedule', {})
        for week_num in sorted(schedule.keys(), key=int):
            week_data = schedule[week_num]
            bye_teams = week_data.get('bye_teams', [])
            games = week_data.get('games', [])

            context_lines.append(f"\nWeek {week_num}:")
            if bye_teams:
                context_lines.append(f"  Bye: {', '.join(bye_teams)}")
            for game in games:
                context_lines.append(f"  {game['away']} at {game['home']}")

        return "\n".join(context_lines)


# Global instance
schedule_manager: Optional[ScheduleManager] = None


def get_schedule_manager() -> ScheduleManager:
    """Get or create the global schedule manager instance"""
    global schedule_manager
    if schedule_manager is None:
        schedule_manager = ScheduleManager()
    return schedule_manager
