"""
Player Lookup Module
Integrates with CollegeFootballData.com API for player stats and recruiting info.
"""

import logging
import os
from typing import Optional, Dict, List, Any
import aiohttp

logger = logging.getLogger(__name__)


class PlayerLookup:
    """Handles player data lookups from CollegeFootballData.com API"""
    
    BASE_URL = "https://api.collegefootballdata.com"
    
    def __init__(self):
        self.api_key = os.getenv('CFB_DATA_API_KEY')
        if not self.api_key:
            logger.warning("⚠️ CFB_DATA_API_KEY not found - player lookup disabled")
    
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
    
    async def search_player(self, name: str, team: Optional[str] = None, year: int = 2025) -> List[Dict[str, Any]]:
        """
        Search for players by name
        
        Args:
            name: Player name to search for
            team: Optional team name to filter by
            year: Season year (default 2025)
            
        Returns:
            List of matching players
        """
        if not self.is_available:
            return []
        
        params = {
            'searchTerm': name,
            'year': year
        }
        if team:
            params['team'] = team
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/player/search",
                    headers=self._get_headers(),
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Player search failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching for player: {e}")
            return []
    
    async def get_roster(self, team: str, year: int = 2025) -> List[Dict[str, Any]]:
        """
        Get full roster for a team
        
        Args:
            team: Team name
            year: Season year
            
        Returns:
            List of players on roster
        """
        if not self.is_available:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/roster",
                    headers=self._get_headers(),
                    params={'team': team, 'year': year}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Roster fetch failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching roster: {e}")
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
                        return self._parse_stats(stats)
                    else:
                        logger.error(f"Stats fetch failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
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
    
    async def get_full_player_info(self, name: str, team: Optional[str] = None, year: int = 2025) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive player info including vitals, stats, and recruiting info
        
        Args:
            name: Player name
            team: Optional team name
            year: Season year
            
        Returns:
            Full player info dictionary or None if not found
        """
        if not self.is_available:
            return None
        
        # Search for the player
        players = await self.search_player(name, team, year)
        
        if not players:
            # Try without team filter
            if team:
                players = await self.search_player(name, year=year)
        
        if not players:
            logger.info(f"No players found matching '{name}'")
            return None
        
        # Get the best match (first result or filter by team if provided)
        player = None
        if team:
            team_lower = team.lower()
            for p in players:
                if team_lower in p.get('team', '').lower():
                    player = p
                    break
        
        if not player:
            player = players[0]
        
        # Get stats for the player
        player_id = player.get('id')
        stats = None
        if player_id:
            stats = await self.get_player_stats(player_id, year)
        
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
            query: Natural language query like "James Smith from Alabama"
            
        Returns:
            Dictionary with 'name' and 'team' keys
        """
        query = query.lower().strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            "what do you know about",
            "tell me about",
            "who is",
            "show me",
            "find",
            "lookup",
            "look up",
            "info on",
            "information on",
            "stats for",
            "stats on",
            "player"
        ]
        
        for prefix in prefixes_to_remove:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
        
        # Handle "from [team]" pattern
        team = None
        if " from " in query:
            parts = query.split(" from ")
            query = parts[0].strip()
            team = parts[1].strip()
        elif " at " in query:
            parts = query.split(" at ")
            query = parts[0].strip()
            team = parts[1].strip()
        elif " on " in query:
            parts = query.split(" on ")
            query = parts[0].strip()
            team = parts[1].strip()
        
        # Clean up team name (remove "the" prefix)
        if team and team.startswith("the "):
            team = team[4:]
        
        # Title case the name
        name = query.title()
        if team:
            team = team.title()
        
        return {
            'name': name,
            'team': team
        }


# Singleton instance
player_lookup = PlayerLookup()

