"""
Player Lookup Module
Integrates with CollegeFootballData.com API for player stats and recruiting info.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class PlayerLookup:
    """Handles player data lookups from CollegeFootballData.com API"""

    BASE_URL = "https://api.collegefootballdata.com"

    def __init__(self):
        self.api_key = os.getenv('CFB_DATA_API_KEY')
        if not self.api_key:
            logger.warning("⚠️ CFB_DATA_API_KEY not found - player lookup disabled")
        else:
            logger.info("✅ CFB_DATA_API_KEY found - player lookup enabled")

    @property
    def is_available(self) -> bool:
        """Check if the API is available"""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authorization"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }

    async def search_player(self, name: str, team: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for players by name

        Args:
            name: Player name to search for
            team: Optional team name to filter by
            year: Season year (optional, tries current and previous years if not specified)

        Returns:
            List of matching players
        """
        if not self.is_available:
            logger.warning("Player lookup not available - no API key")
            return []

        # If no year specified, try current year and previous years
        years_to_try = [year] if year else [2025, 2024, 2023]

        for try_year in years_to_try:
            params = {'searchTerm': name}
            if try_year:
                params['year'] = try_year
            if team:
                params['team'] = team

            logger.info(f"🔍 Searching CFBD API: {params}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.BASE_URL}/player/search",
                        headers=self._get_headers(),
                        params=params
                    ) as response:
                        response_text = await response.text()
                        logger.info(f"🔍 CFBD API response status: {response.status}")

                        if response.status == 200:
                            data = await response.json() if response_text else []
                            if data:
                                logger.info(f"✅ Found {len(data)} players for year {try_year}")
                                return data
                            else:
                                logger.info(f"No players found for year {try_year}, trying next...")
                        elif response.status == 401:
                            logger.error(f"❌ CFBD API auth failed (401): {response_text[:200]}")
                            return []
                        else:
                            logger.error(f"❌ CFBD API error ({response.status}): {response_text[:200]}")
            except Exception as e:
                logger.error(f"❌ Error searching for player: {e}", exc_info=True)

        return []

    async def get_roster(self, team: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get full roster for a team

        Args:
            team: Team name
            year: Season year (optional, tries multiple years)

        Returns:
            List of players on roster
        """
        if not self.is_available:
            return []

        years_to_try = [year] if year else [2025, 2024, 2023]

        for try_year in years_to_try:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.BASE_URL}/roster",
                        headers=self._get_headers(),
                        params={'team': team, 'year': try_year}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data:
                                logger.info(f"✅ Found roster for {team} ({try_year}): {len(data)} players")
                                return data
                        else:
                            response_text = await response.text()
                            logger.error(f"Roster fetch failed ({response.status}): {response_text[:200]}")
            except Exception as e:
                logger.error(f"Error fetching roster: {e}", exc_info=True)

        return []

    async def get_player_stats(self, player_id: int, year: int = 2025) -> Optional[Dict[str, Any]]:
        """
        Get season stats for a specific player

        Args:
            player_id: Player ID from search results
            year: Season year

        Returns:
            Player stats dictionary
        """
        if not self.is_available:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                # Get player season stats
                async with session.get(
                    f"{self.BASE_URL}/stats/player/season",
                    headers=self._get_headers(),
                    params={'year': year, 'playerId': player_id}
                ) as response:
                    if response.status == 200:
                        stats = await response.json()
                        if stats:
                            logger.info(f"✅ Found {len(stats)} stat entries for player {player_id}")
                        return self._parse_stats(stats)
                    else:
                        response_text = await response.text()
                        logger.warning(f"Stats fetch returned {response.status}: {response_text[:100]}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}", exc_info=True)
            return None

    async def get_recruiting_info(self, player_name: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get recruiting info for a player

        Args:
            player_name: Player name to search
            year: Recruiting class year (optional)

        Returns:
            Recruiting info dictionary
        """
        if not self.is_available:
            return None

        params = {}
        if year:
            params['year'] = year

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/recruiting/players",
                    headers=self._get_headers(),
                    params=params
                ) as response:
                    if response.status == 200:
                        recruits = await response.json()
                        # Search for matching name
                        for recruit in recruits:
                            if player_name.lower() in recruit.get('name', '').lower():
                                return recruit
                        return None
                    else:
                        logger.error(f"Recruiting fetch failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching recruiting info: {e}")
            return None

    def _parse_stats(self, raw_stats: List[Dict]) -> Dict[str, Any]:
        """
        Parse raw stats into a cleaner format

        Args:
            raw_stats: Raw stats from API

        Returns:
            Parsed stats dictionary
        """
        parsed = {
            'passing': {},
            'rushing': {},
            'receiving': {},
            'defense': {},
            'kicking': {}
        }

        for stat_entry in raw_stats:
            category = stat_entry.get('category', '').lower()
            stat_type = stat_entry.get('statType', '')
            stat_value = stat_entry.get('stat', 0)

            if 'pass' in category:
                parsed['passing'][stat_type] = stat_value
            elif 'rush' in category:
                parsed['rushing'][stat_type] = stat_value
            elif 'receiv' in category:
                parsed['receiving'][stat_type] = stat_value
            elif category in ['defense', 'defensive', 'tackles', 'interceptions']:
                parsed['defense'][stat_type] = stat_value
            elif 'kick' in category or 'punt' in category:
                parsed['kicking'][stat_type] = stat_value

        return parsed

    async def get_full_player_info(self, name: str, team: Optional[str] = None, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive player info including vitals, stats, and recruiting info

        Args:
            name: Player name
            team: Optional team name
            year: Season year (optional, will try multiple years)

        Returns:
            Full player info dictionary or None if not found
        """
        if not self.is_available:
            logger.warning("Player lookup not available - no API key configured")
            return None

        logger.info(f"🔍 Looking up player: {name}" + (f" from {team}" if team else ""))

        # Search for the player (will try multiple years automatically)
        players = await self.search_player(name, team, year)

        if not players and team:
            # Try without team filter
            logger.info(f"No results with team filter, trying without...")
            players = await self.search_player(name, year=year)

        if not players:
            logger.info(f"❌ No players found matching '{name}'")
            return None

        logger.info(f"✅ Found {len(players)} potential matches")

        # Get the best match (first result or filter by team if provided)
        player = None
        if team:
            team_lower = team.lower()
            for p in players:
                if team_lower in p.get('team', '').lower():
                    player = p
                    logger.info(f"✅ Matched player to team: {p.get('name')} - {p.get('team')}")
                    break

        if not player:
            player = players[0]
            logger.info(f"✅ Using first result: {player.get('name')} - {player.get('team')}")

        # Get stats for the player
        player_id = player.get('id')
        stats = None
        if player_id:
            # Try stats for multiple years
            for stat_year in [2025, 2024, 2023]:
                stats = await self.get_player_stats(player_id, stat_year)
                if stats and any(stats.values()):
                    logger.info(f"✅ Found stats for year {stat_year}")
                    break

        # Try to get recruiting info
        recruiting = await self.get_recruiting_info(name)

        return {
            'player': player,
            'stats': stats,
            'recruiting': recruiting
        }

    def format_player_response(self, player_info: Dict[str, Any]) -> str:
        """
        Format player info into a nice Discord response

        Args:
            player_info: Full player info from get_full_player_info

        Returns:
            Formatted string for Discord
        """
        if not player_info:
            return "Couldn't find that player, mate. Check the spelling or try another name."

        player = player_info.get('player', {})
        stats = player_info.get('stats')
        recruiting = player_info.get('recruiting')

        # Basic info
        name = player.get('name', player.get('firstName', '') + ' ' + player.get('lastName', ''))
        team = player.get('team', 'Unknown')
        position = player.get('position', 'Unknown')

        # Physical attributes
        height = player.get('height')
        weight = player.get('weight')
        year_str = player.get('year', '')

        # Format height (usually in inches from API)
        if height:
            if isinstance(height, (int, float)) and height > 12:
                feet = int(height) // 12
                inches = int(height) % 12
                height_fmt = f"{feet}'{inches}\""
            else:
                height_fmt = str(height)
        else:
            height_fmt = "N/A"

        weight_fmt = f"{weight}lbs" if weight else "N/A"

        # Build response
        response_parts = []

        # Header
        response_parts.append(f"🏈 **{name}** - {team}")
        response_parts.append(f"**Position:** {position} | **Year:** {year_str} | **{height_fmt}** {weight_fmt}")

        # Hometown if available
        hometown = player.get('homeCity', '')
        home_state = player.get('homeState', '')
        if hometown or home_state:
            location = ', '.join(filter(None, [hometown, home_state]))
            response_parts.append(f"**Hometown:** {location}")

        response_parts.append("")  # Blank line

        # Stats section
        if stats:
            defense = stats.get('defense', {})
            passing = stats.get('passing', {})
            rushing = stats.get('rushing', {})
            receiving = stats.get('receiving', {})

            # Defensive stats
            if defense:
                tackles = defense.get('TOT', defense.get('SOLO', 0))
                solo = defense.get('SOLO', 0)
                tfl = defense.get('TFL', 0)
                sacks = defense.get('SACKS', defense.get('SK', 0))
                ints = defense.get('INT', 0)

                stat_line = []
                if tackles or solo:
                    stat_line.append(f"{solo} Solo")
                if tfl:
                    stat_line.append(f"{tfl} TFL")
                if sacks:
                    stat_line.append(f"{sacks} Sacks")
                if ints:
                    stat_line.append(f"{ints} INT")

                if stat_line:
                    response_parts.append(f"📊 **2025 Season Stats:**")
                    response_parts.append(" | ".join(stat_line))

            # Passing stats
            elif passing:
                comp = passing.get('COMPLETIONS', 0)
                att = passing.get('ATT', 0)
                yards = passing.get('YDS', 0)
                tds = passing.get('TD', 0)
                ints = passing.get('INT', 0)

                response_parts.append(f"📊 **2025 Season Stats:**")
                response_parts.append(f"{comp}/{att} | {yards} YDS | {tds} TD | {ints} INT")

            # Rushing stats
            elif rushing:
                carries = rushing.get('CAR', 0)
                yards = rushing.get('YDS', 0)
                tds = rushing.get('TD', 0)
                avg = rushing.get('AVG', 0)

                response_parts.append(f"📊 **2025 Season Stats:**")
                response_parts.append(f"{carries} CAR | {yards} YDS | {avg} AVG | {tds} TD")

            # Receiving stats
            elif receiving:
                rec = receiving.get('REC', 0)
                yards = receiving.get('YDS', 0)
                tds = receiving.get('TD', 0)
                avg = receiving.get('AVG', 0)

                response_parts.append(f"📊 **2025 Season Stats:**")
                response_parts.append(f"{rec} REC | {yards} YDS | {avg} AVG | {tds} TD")
        else:
            response_parts.append("📊 *No stats available for this season*")

        # Recruiting info
        if recruiting:
            response_parts.append("")
            stars = recruiting.get('stars', 0)
            rating = recruiting.get('rating', 0)
            ranking = recruiting.get('ranking', 'N/A')

            star_display = "⭐" * stars if stars else "N/A"
            response_parts.append(f"🎯 **Recruiting:** {star_display} ({rating:.4f})" if rating else f"🎯 **Recruiting:** {star_display}")
            if ranking and ranking != 'N/A':
                response_parts.append(f"**National Rank:** #{ranking}")

        return "\n".join(response_parts)

    def parse_player_query(self, query: str) -> Dict[str, Optional[str]]:
        """
        Parse a natural language query for player info

        Args:
            query: Natural language query like "@Harry what do you know about James Smith from Alabama"

        Returns:
            Dictionary with 'name' and 'team' keys
        """
        import re

        query = query.strip()

        # Remove Discord mentions (format: <@123456789> or <@!123456789>)
        query = re.sub(r'<@!?\d+>', '', query)

        # Remove any remaining @ mentions (like @Harry)
        query = re.sub(r'@\w+', '', query)

        query = query.lower().strip()

        logger.info(f"🔍 Parsing player query: '{query}'")

        # Remove common prefixes (order matters - longer/more specific first)
        prefixes_to_remove = [
            # Question formats
            "what do you know about",
            "what can you tell me about",
            "what are the stats for",
            "what are the stats on",
            "do you have info on",
            "do you have any info on",
            "can you tell me about",
            "can you look up",
            "can you find",
            "could you look up",
            "any info on",
            "got any info on",
            # Command formats
            "tell me about",
            "give me info on",
            "give me stats for",
            "give me stats on",
            "get me stats for",
            "get me stats on",
            "get me info on",
            "pull up",
            "pull stats for",
            "show me stats for",
            "show me stats on",
            "show me info on",
            "show me",
            "look up",
            "lookup",
            "find me",
            "find",
            # Simple formats
            "information on",
            "info on",
            "stats for",
            "stats on",
            "player info for",
            "player stats for",
            "player info",
            "player stats",
            "who is",
            "who's",
            "player",
        ]

        for prefix in prefixes_to_remove:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                logger.info(f"🔍 After removing '{prefix}': '{query}'")
                break  # Only remove one prefix

        # Handle team patterns (check in order of specificity)
        team = None
        team_patterns = [
            " who plays for ",
            " that plays for ",
            " playing for ",
            " plays for ",
            " from ",
            " at ",
            " on ",
            ", ",  # "James Smith, Alabama"
        ]

        for pattern in team_patterns:
            if pattern in query:
                parts = query.split(pattern, 1)
                query = parts[0].strip()
                team = parts[1].strip()
                logger.info(f"🔍 Found team pattern '{pattern.strip()}': name='{query}', team='{team}'")
                break

        # Clean up team name (remove common prefixes and trailing punctuation)
        if team:
            team_prefixes = ["the ", "team "]
            for tp in team_prefixes:
                if team.startswith(tp):
                    team = team[len(tp):]
            team = team.rstrip('?.!').strip()

        # Title case the name and clean up
        name = query.title().strip()
        if team:
            team = team.title().strip()

        logger.info(f"✅ Parsed player query: name='{name}', team='{team}'")

        return {
            'name': name,
            'team': team
        }


# Singleton instance
player_lookup = PlayerLookup()
