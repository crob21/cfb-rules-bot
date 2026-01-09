"""
Player Lookup Module
Integrates with CollegeFootballData.com API using the official cfbd library.
"""

import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import cfbd library
try:
    import cfbd
    from cfbd.rest import ApiException
    CFBD_AVAILABLE = True
except ImportError:
    CFBD_AVAILABLE = False
    logger.warning("⚠️ cfbd library not installed - player lookup disabled")


class PlayerLookup:
    """Handles player data lookups from CollegeFootballData.com API using official library"""

    def __init__(self):
        self.api_key = os.getenv('CFB_DATA_API_KEY')
        self._api_client = None
        self._players_api = None
        self._stats_api = None
        self._recruiting_api = None
        self._teams_api = None

        if not CFBD_AVAILABLE:
            logger.warning("⚠️ cfbd library not available - player lookup disabled")
            return

        if not self.api_key:
            logger.warning("⚠️ CFB_DATA_API_KEY not found - player lookup disabled")
            return

        # Configure the API client
        try:
            configuration = cfbd.Configuration(
                access_token=self.api_key
            )
            self._api_client = cfbd.ApiClient(configuration)
            self._players_api = cfbd.PlayersApi(self._api_client)
            self._stats_api = cfbd.StatsApi(self._api_client)
            self._recruiting_api = cfbd.RecruitingApi(self._api_client)
            self._teams_api = cfbd.TeamsApi(self._api_client)
            logger.info("✅ CFBD API configured successfully")
        except Exception as e:
            logger.error(f"❌ Failed to configure CFBD API: {e}")
            self._api_client = None

    @property
    def is_available(self) -> bool:
        """Check if the API is available"""
        return CFBD_AVAILABLE and self._api_client is not None

    async def search_player(self, name: str, team: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for players by name using official API

        Args:
            name: Player name to search for
            team: Optional team name to filter by
            year: Season year (optional)

        Returns:
            List of matching players
        """
        if not self.is_available:
            logger.warning("Player lookup not available")
            return []

        years_to_try = [year] if year else [2024, 2023, 2022]

        for try_year in years_to_try:
            try:
                logger.info(f"🔍 Searching CFBD for '{name}' (year={try_year}, team={team})")

                # Run sync API call in thread pool
                kwargs = {'search_term': name, 'year': try_year}
                if team:
                    kwargs['team'] = team

                results = await asyncio.to_thread(
                    self._players_api.search_players,
                    **kwargs
                )

                if results:
                    # Convert to dicts
                    players = [self._player_to_dict(p) for p in results]
                    logger.info(f"✅ Found {len(players)} players for year {try_year}")
                    return players
                else:
                    logger.info(f"No results for year {try_year}, trying next...")

            except ApiException as e:
                logger.error(f"❌ CFBD API error: {e.status} - {e.reason}")
                if e.status == 401:
                    logger.error("Authentication failed - check your API key")
                    return []
            except Exception as e:
                logger.error(f"❌ Error searching for player: {e}", exc_info=True)

        return []

    def _player_to_dict(self, player) -> Dict[str, Any]:
        """Convert cfbd PlayerSearchResult to dict"""
        return {
            'id': getattr(player, 'id', None),
            'name': getattr(player, 'name', None),
            'firstName': getattr(player, 'first_name', None),
            'lastName': getattr(player, 'last_name', None),
            'team': getattr(player, 'team', None),
            'position': getattr(player, 'position', None),
            'height': getattr(player, 'height', None),
            'weight': getattr(player, 'weight', None),
            'year': getattr(player, 'year', None),
            'jersey': getattr(player, 'jersey', None),
            'homeCity': getattr(player, 'home_city', None),
            'homeState': getattr(player, 'home_state', None),
            'homeCountry': getattr(player, 'home_country', None),
        }

    async def get_roster(self, team: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get full roster for a team

        Args:
            team: Team name
            year: Season year (optional)

        Returns:
            List of players on roster
        """
        if not self.is_available:
            return []

        years_to_try = [year] if year else [2024, 2023]

        for try_year in years_to_try:
            try:
                logger.info(f"🔍 Fetching roster for {team} ({try_year})")

                results = await asyncio.to_thread(
                    self._teams_api.get_roster,
                    team=team,
                    year=try_year
                )

                if results:
                    roster = [self._roster_player_to_dict(p) for p in results]
                    logger.info(f"✅ Found {len(roster)} players on {team} roster")
                    return roster

            except ApiException as e:
                logger.error(f"❌ CFBD API error: {e.status} - {e.reason}")
            except Exception as e:
                logger.error(f"❌ Error fetching roster: {e}", exc_info=True)

        return []

    def _roster_player_to_dict(self, player) -> Dict[str, Any]:
        """Convert cfbd RosterPlayer to dict"""
        return {
            'id': getattr(player, 'id', None),
            'name': f"{getattr(player, 'first_name', '')} {getattr(player, 'last_name', '')}".strip(),
            'firstName': getattr(player, 'first_name', None),
            'lastName': getattr(player, 'last_name', None),
            'team': getattr(player, 'team', None),
            'position': getattr(player, 'position', None),
            'height': getattr(player, 'height', None),
            'weight': getattr(player, 'weight', None),
            'year': getattr(player, 'year', None),
            'jersey': getattr(player, 'jersey', None),
            'homeCity': getattr(player, 'home_city', None),
            'homeState': getattr(player, 'home_state', None),
            'homeCountry': getattr(player, 'home_country', None),
        }

    async def get_player_stats(self, player_name: str, team: str, year: int = 2024) -> Optional[Dict[str, Any]]:
        """
        Get season stats for a specific player

        Args:
            player_name: Player name to search for
            team: Team name
            year: Season year

        Returns:
            Player stats dictionary
        """
        if not self.is_available:
            return None

        logger.info(f"🔍 Fetching stats for {player_name} on {team} ({year})")

        try:
            # Get all player stats for the team
            results = await asyncio.to_thread(
                self._stats_api.get_player_season_stats,
                year=year,
                team=team
            )

            if results:
                logger.info(f"✅ Found {len(results)} stat entries for {team}")

                # Filter for the specific player (case-insensitive partial match)
                player_stats = [
                    s for s in results
                    if player_name.lower() in getattr(s, 'player', '').lower()
                ]

                if player_stats:
                    logger.info(f"✅ Found {len(player_stats)} stat entries for {player_name}")
                    return self._parse_stats(player_stats)
                else:
                    logger.info(f"No stats found for {player_name} in team stats")

            return None

        except ApiException as e:
            logger.error(f"❌ CFBD API error: {e.status} - {e.reason}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching player stats: {e}", exc_info=True)
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

        # Try multiple recruiting classes
        years_to_try = [year] if year else [2024, 2023, 2022, 2021]

        for try_year in years_to_try:
            try:
                logger.info(f"🔍 Searching recruiting data for '{player_name}' ({try_year})")

                results = await asyncio.to_thread(
                    self._recruiting_api.get_recruits,
                    year=try_year
                )

                if results:
                    # Search for matching name (partial, case-insensitive)
                    for recruit in results:
                        recruit_name = getattr(recruit, 'name', '')
                        if player_name.lower() in recruit_name.lower():
                            logger.info(f"✅ Found recruiting info for {recruit_name}")
                            return {
                                'name': recruit_name,
                                'school': getattr(recruit, 'committed_to', None),
                                'position': getattr(recruit, 'position', None),
                                'stars': getattr(recruit, 'stars', None),
                                'rating': getattr(recruit, 'rating', None),
                                'ranking': getattr(recruit, 'ranking', None),
                                'stateRank': getattr(recruit, 'state_rank', None),
                                'positionRank': getattr(recruit, 'position_rank', None),
                                'city': getattr(recruit, 'city', None),
                                'state': getattr(recruit, 'state_province', None),
                                'height': getattr(recruit, 'height', None),
                                'weight': getattr(recruit, 'weight', None),
                                'year': try_year,
                            }

            except ApiException as e:
                logger.warning(f"Recruiting API error for {try_year}: {e.status}")
            except Exception as e:
                logger.error(f"❌ Error fetching recruiting info: {e}", exc_info=True)

        return None

    async def get_transfer_portal(self, year: int = 2024) -> List[Dict[str, Any]]:
        """
        Get transfer portal data for a year

        Args:
            year: Transfer portal year

        Returns:
            List of transfer portal entries
        """
        if not self.is_available:
            return []

        try:
            logger.info(f"🔍 Fetching transfer portal data ({year})")

            results = await asyncio.to_thread(
                self._players_api.get_transfer_portal,
                year=year
            )

            if results:
                transfers = []
                for t in results:
                    transfers.append({
                        'name': f"{getattr(t, 'first_name', '')} {getattr(t, 'last_name', '')}".strip(),
                        'position': getattr(t, 'position', None),
                        'origin': getattr(t, 'origin', None),
                        'destination': getattr(t, 'destination', None),
                        'transferDate': getattr(t, 'transfer_date', None),
                        'rating': getattr(t, 'rating', None),
                        'stars': getattr(t, 'stars', None),
                        'eligibility': getattr(t, 'eligibility', None),
                    })
                logger.info(f"✅ Found {len(transfers)} transfer portal entries")
                return transfers

        except ApiException as e:
            logger.error(f"❌ CFBD API error: {e.status} - {e.reason}")
        except Exception as e:
            logger.error(f"❌ Error fetching transfer portal: {e}", exc_info=True)

        return []

    async def search_transfer(self, player_name: str, year: int = 2024) -> Optional[Dict[str, Any]]:
        """
        Search for a player in the transfer portal

        Args:
            player_name: Player name to search
            year: Transfer portal year

        Returns:
            Transfer info or None
        """
        transfers = await self.get_transfer_portal(year)

        for t in transfers:
            if player_name.lower() in t.get('name', '').lower():
                logger.info(f"✅ Found transfer info for {t.get('name')}")
                return t

        # Try previous year
        if year > 2022:
            transfers = await self.get_transfer_portal(year - 1)
            for t in transfers:
                if player_name.lower() in t.get('name', '').lower():
                    logger.info(f"✅ Found transfer info for {t.get('name')} ({year-1})")
                    return t

        return None

    def _parse_stats(self, raw_stats: List) -> Dict[str, Any]:
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
            'kicking': {},
            'punting': {},
            'returns': {},
        }

        for stat_entry in raw_stats:
            category = getattr(stat_entry, 'category', '').lower()
            stat_type = getattr(stat_entry, 'stat_type', '')
            stat_value = getattr(stat_entry, 'stat', 0)

            if 'pass' in category:
                parsed['passing'][stat_type] = stat_value
            elif 'rush' in category:
                parsed['rushing'][stat_type] = stat_value
            elif 'receiv' in category:
                parsed['receiving'][stat_type] = stat_value
            elif category in ['defense', 'defensive', 'tackles', 'interceptions', 'fumbles']:
                parsed['defense'][stat_type] = stat_value
            elif 'kick' in category and 'return' not in category:
                parsed['kicking'][stat_type] = stat_value
            elif 'punt' in category and 'return' not in category:
                parsed['punting'][stat_type] = stat_value
            elif 'return' in category:
                parsed['returns'][stat_type] = stat_value

        return parsed

    async def get_full_player_info(self, name: str, team: Optional[str] = None, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive player info including vitals, stats, recruiting, and transfer info

        Args:
            name: Player name
            team: Optional team name
            year: Season year (optional)

        Returns:
            Full player info dictionary or None if not found
        """
        if not self.is_available:
            logger.warning("Player lookup not available - no API configured")
            return None

        logger.info(f"🔍 Looking up player: {name}" + (f" from {team}" if team else ""))

        # Search for the player
        players = await self.search_player(name, team, year)

        if not players and team:
            # Try without team filter
            logger.info("No results with team filter, trying without...")
            players = await self.search_player(name, year=year)

        if not players:
            logger.info(f"❌ No players found matching '{name}'")
            return None

        logger.info(f"✅ Found {len(players)} potential matches")

        # Get the best match
        player = None
        if team:
            team_lower = team.lower()
            for p in players:
                if team_lower in (p.get('team') or '').lower():
                    player = p
                    logger.info(f"✅ Matched player to team: {p.get('name')} - {p.get('team')}")
                    break

        if not player:
            player = players[0]
            logger.info(f"✅ Using first result: {player.get('name')} - {player.get('team')}")

        # Get additional info in parallel
        player_name = player.get('name', name)
        player_team = player.get('team', team or '')

        # Fetch stats, recruiting, and transfer info concurrently
        stats = None
        recruiting = None
        transfer = None

        tasks = []

        if player_team:
            # Stats for multiple years
            async def get_stats():
                for stat_year in [2024, 2023, 2022]:
                    s = await self.get_player_stats(player_name, player_team, stat_year)
                    if s and any(v for v in s.values() if v):
                        return s
                return None

            tasks.append(('stats', get_stats()))

        tasks.append(('recruiting', self.get_recruiting_info(player_name)))
        tasks.append(('transfer', self.search_transfer(player_name)))

        # Run all tasks concurrently
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        for i, (task_name, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Error in {task_name}: {result}")
            elif task_name == 'stats':
                stats = result
            elif task_name == 'recruiting':
                recruiting = result
            elif task_name == 'transfer':
                transfer = result

        return {
            'player': player,
            'stats': stats,
            'recruiting': recruiting,
            'transfer': transfer,
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
        transfer = player_info.get('transfer')

        # Basic info
        name = player.get('name') or f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
        team = player.get('team', 'Unknown')
        position = player.get('position', 'Unknown')

        # Physical attributes
        height = player.get('height')
        weight = player.get('weight')
        year_str = player.get('year', '')
        jersey = player.get('jersey')

        # Format height
        if height:
            if isinstance(height, (int, float)) and height > 12:
                feet = int(height) // 12
                inches = int(height) % 12
                height_fmt = f"{feet}'{inches}\""
            else:
                height_fmt = str(height)
        else:
            height_fmt = None

        weight_fmt = f"{weight}lbs" if weight else None

        # Build response
        response_parts = []

        # Header
        response_parts.append(f"🏈 **{name}** - {team}")

        # Vitals line
        vitals = []
        if position:
            vitals.append(f"**Position:** {position}")
        if jersey:
            vitals.append(f"**#**{jersey}")
        if year_str:
            vitals.append(f"**Year:** {year_str}")
        if height_fmt:
            vitals.append(f"**{height_fmt}**")
        if weight_fmt:
            vitals.append(f"**{weight_fmt}**")

        if vitals:
            response_parts.append(" | ".join(vitals))

        # Hometown
        hometown = player.get('homeCity', '')
        home_state = player.get('homeState', '')
        if hometown or home_state:
            location = ', '.join(filter(None, [hometown, home_state]))
            response_parts.append(f"📍 {location}")

        response_parts.append("")

        # Transfer info (if applicable)
        if transfer:
            origin = transfer.get('origin', 'Unknown')
            destination = transfer.get('destination', 'Unknown')
            response_parts.append(f"🔄 **Transfer:** {origin} → {destination}")
            if transfer.get('eligibility'):
                response_parts.append(f"   Eligibility: {transfer.get('eligibility')}")
            response_parts.append("")

        # Stats section
        if stats:
            has_stats = False

            # Passing
            passing = stats.get('passing', {})
            if passing:
                comp = passing.get('COMPLETIONS', passing.get('completions', 0))
                att = passing.get('ATT', passing.get('attempts', 0))
                yards = passing.get('YDS', passing.get('yards', 0))
                tds = passing.get('TD', passing.get('touchdowns', 0))
                ints = passing.get('INT', passing.get('interceptions', 0))
                if any([comp, yards, tds]):
                    response_parts.append("📊 **Passing:**")
                    response_parts.append(f"   {comp}/{att} | {yards} YDS | {tds} TD | {ints} INT")
                    has_stats = True

            # Rushing
            rushing = stats.get('rushing', {})
            if rushing:
                carries = rushing.get('CAR', rushing.get('carries', 0))
                yards = rushing.get('YDS', rushing.get('yards', 0))
                tds = rushing.get('TD', rushing.get('touchdowns', 0))
                if any([carries, yards, tds]):
                    response_parts.append("📊 **Rushing:**")
                    response_parts.append(f"   {carries} CAR | {yards} YDS | {tds} TD")
                    has_stats = True

            # Receiving
            receiving = stats.get('receiving', {})
            if receiving:
                rec = receiving.get('REC', receiving.get('receptions', 0))
                yards = receiving.get('YDS', receiving.get('yards', 0))
                tds = receiving.get('TD', receiving.get('touchdowns', 0))
                if any([rec, yards, tds]):
                    response_parts.append("📊 **Receiving:**")
                    response_parts.append(f"   {rec} REC | {yards} YDS | {tds} TD")
                    has_stats = True

            # Defense
            defense = stats.get('defense', {})
            if defense:
                tackles = defense.get('TOT', defense.get('SOLO', defense.get('tackles', 0)))
                solo = defense.get('SOLO', 0)
                tfl = defense.get('TFL', 0)
                sacks = defense.get('SACKS', defense.get('SK', 0))
                ints = defense.get('INT', 0)
                if any([tackles, solo, tfl, sacks, ints]):
                    response_parts.append("📊 **Defense:**")
                    stat_parts = []
                    if solo:
                        stat_parts.append(f"{solo} Solo")
                    if tfl:
                        stat_parts.append(f"{tfl} TFL")
                    if sacks:
                        stat_parts.append(f"{sacks} Sacks")
                    if ints:
                        stat_parts.append(f"{ints} INT")
                    response_parts.append(f"   {' | '.join(stat_parts)}")
                    has_stats = True

            if not has_stats:
                response_parts.append("📊 *No stats recorded this season*")
        else:
            response_parts.append("📊 *No stats available*")

        # Recruiting info
        if recruiting:
            response_parts.append("")
            stars = recruiting.get('stars', 0)
            rating = recruiting.get('rating', 0)
            ranking = recruiting.get('ranking')
            pos_rank = recruiting.get('positionRank')
            state_rank = recruiting.get('stateRank')

            star_display = "⭐" * stars if stars else "N/R"

            if rating:
                response_parts.append(f"🎯 **Recruiting:** {star_display} ({rating:.4f})")
            else:
                response_parts.append(f"🎯 **Recruiting:** {star_display}")

            ranks = []
            if ranking:
                ranks.append(f"#{ranking} National")
            if pos_rank:
                ranks.append(f"#{pos_rank} {recruiting.get('position', 'Pos')}")
            if state_rank:
                ranks.append(f"#{state_rank} {recruiting.get('state', 'State')}")

            if ranks:
                response_parts.append(f"   {' | '.join(ranks)}")

        return "\n".join(response_parts)

    def parse_player_query(self, query: str) -> Dict[str, Optional[str]]:
        """
        Parse a natural language query for player info

        Args:
            query: Natural language query like "@Harry what do you know about James Smith from Alabama"

        Returns:
            Dictionary with 'name' and 'team' keys
        """
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
