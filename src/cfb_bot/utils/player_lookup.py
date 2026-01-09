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


class CFBDataLookup:
    """
    Comprehensive CFB data lookups from CollegeFootballData.com API.
    
    Features:
    - Player search and stats
    - Team rosters and info
    - Rankings (AP, Coaches, CFP)
    - Matchup history
    - Game schedules and results
    - NFL Draft picks
    - Transfer portal
    - Betting lines
    - Advanced stats (SP+, SRS, Elo)
    """

    def __init__(self):
        self.api_key = os.getenv('CFB_DATA_API_KEY')
        self._api_client = None
        
        # API instances
        self._players_api = None
        self._stats_api = None
        self._recruiting_api = None
        self._teams_api = None
        self._games_api = None
        self._rankings_api = None
        self._betting_api = None
        self._ratings_api = None
        self._draft_api = None

        if not CFBD_AVAILABLE:
            logger.warning("⚠️ cfbd library not available - CFB data disabled")
            return

        if not self.api_key:
            logger.warning("⚠️ CFB_DATA_API_KEY not found - CFB data disabled")
            return

        # Configure the API client
        try:
            configuration = cfbd.Configuration(
                access_token=self.api_key
            )
            self._api_client = cfbd.ApiClient(configuration)
            
            # Initialize all API instances
            self._players_api = cfbd.PlayersApi(self._api_client)
            self._stats_api = cfbd.StatsApi(self._api_client)
            self._recruiting_api = cfbd.RecruitingApi(self._api_client)
            self._teams_api = cfbd.TeamsApi(self._api_client)
            self._games_api = cfbd.GamesApi(self._api_client)
            self._rankings_api = cfbd.RankingsApi(self._api_client)
            self._betting_api = cfbd.BettingApi(self._api_client)
            self._ratings_api = cfbd.RatingsApi(self._api_client)
            self._draft_api = cfbd.DraftApi(self._api_client)
            
            logger.info("✅ CFBD API configured successfully with all endpoints")
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

        years_to_try = [year] if year else [2025, 2024, 2023]

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

        years_to_try = [year] if year else [2025, 2024, 2023]

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
        years_to_try = [year] if year else [2025, 2024, 2023, 2022]

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
            # Stats for ALL available years
            async def get_all_stats():
                all_stats = {}
                for stat_year in [2025, 2024, 2023, 2022, 2021]:
                    s = await self.get_player_stats(player_name, player_team, stat_year)
                    if s and any(v for v in s.values() if v):
                        logger.info(f"✅ Found stats for {stat_year} season")
                        all_stats[stat_year] = s
                return all_stats if all_stats else None

            tasks.append(('stats', get_all_stats()))

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

        # Stats section (multi-year)
        if stats and isinstance(stats, dict):
            has_any_stats = False

            # Sort years descending (most recent first)
            for year in sorted(stats.keys(), reverse=True):
                year_stats = stats[year]
                year_has_stats = False
                year_parts = []

                # Passing
                passing = year_stats.get('passing', {})
                if passing:
                    comp = passing.get('COMPLETIONS', passing.get('completions', 0))
                    att = passing.get('ATT', passing.get('attempts', 0))
                    yards = passing.get('YDS', passing.get('yards', 0))
                    tds = passing.get('TD', passing.get('touchdowns', 0))
                    ints = passing.get('INT', passing.get('interceptions', 0))
                    if any([comp, yards, tds]):
                        year_parts.append(f"🏈 {comp}/{att} | {yards} YDS | {tds} TD | {ints} INT")
                        year_has_stats = True

                # Rushing
                rushing = year_stats.get('rushing', {})
                if rushing:
                    carries = rushing.get('CAR', rushing.get('carries', 0))
                    yards = rushing.get('YDS', rushing.get('yards', 0))
                    tds = rushing.get('TD', rushing.get('touchdowns', 0))
                    if any([carries, yards, tds]):
                        year_parts.append(f"🏃 {carries} CAR | {yards} YDS | {tds} TD")
                        year_has_stats = True

                # Receiving
                receiving = year_stats.get('receiving', {})
                if receiving:
                    rec = receiving.get('REC', receiving.get('receptions', 0))
                    yards = receiving.get('YDS', receiving.get('yards', 0))
                    tds = receiving.get('TD', receiving.get('touchdowns', 0))
                    if any([rec, yards, tds]):
                        year_parts.append(f"🎯 {rec} REC | {yards} YDS | {tds} TD")
                        year_has_stats = True

                # Defense
                defense = year_stats.get('defense', {})
                if defense:
                    tackles = defense.get('TOT', defense.get('SOLO', defense.get('tackles', 0)))
                    solo = defense.get('SOLO', 0)
                    tfl = defense.get('TFL', 0)
                    sacks = defense.get('SACKS', defense.get('SK', 0))
                    ints = defense.get('INT', 0)
                    if any([tackles, solo, tfl, sacks, ints]):
                        stat_parts = []
                        if solo:
                            stat_parts.append(f"{solo} Solo")
                        if tfl:
                            stat_parts.append(f"{tfl} TFL")
                        if sacks:
                            stat_parts.append(f"{sacks} Sacks")
                        if ints:
                            stat_parts.append(f"{ints} INT")
                        year_parts.append(f"🛡️ {' | '.join(stat_parts)}")
                        year_has_stats = True

                # Kicking
                kicking = year_stats.get('kicking', {})
                if kicking:
                    fgm = kicking.get('FGM', 0)
                    fga = kicking.get('FGA', 0)
                    xpm = kicking.get('XPM', 0)
                    if any([fgm, fga, xpm]):
                        year_parts.append(f"🦵 {fgm}/{fga} FG | {xpm} XP")
                        year_has_stats = True

                if year_has_stats:
                    response_parts.append(f"📊 **{year} Season:**")
                    for part in year_parts:
                        response_parts.append(f"   {part}")
                    has_any_stats = True

            if not has_any_stats:
                response_parts.append("📊 *No stats recorded*")
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

    # ==================== TEAM FEATURES ====================

    async def get_team_info(self, team: str) -> Optional[Dict[str, Any]]:
        """Get basic team information"""
        if not self.is_available:
            return None

        try:
            results = await asyncio.to_thread(
                self._teams_api.get_teams,
                conference=None
            )
            
            if results:
                team_lower = team.lower()
                for t in results:
                    if (team_lower in getattr(t, 'school', '').lower() or 
                        team_lower in getattr(t, 'mascot', '').lower()):
                        return {
                            'school': getattr(t, 'school', None),
                            'mascot': getattr(t, 'mascot', None),
                            'abbreviation': getattr(t, 'abbreviation', None),
                            'conference': getattr(t, 'conference', None),
                            'division': getattr(t, 'division', None),
                            'color': getattr(t, 'color', None),
                            'alt_color': getattr(t, 'alt_color', None),
                            'logos': getattr(t, 'logos', []),
                        }
            return None
        except Exception as e:
            logger.error(f"Error getting team info: {e}")
            return None

    async def get_rankings(self, year: int = 2025, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get team rankings (AP, Coaches, CFP)
        
        Returns list of polls with their rankings
        """
        if not self.is_available:
            return []

        try:
            logger.info(f"🔍 Fetching rankings for {year}" + (f" week {week}" if week else ""))
            
            kwargs = {'year': year}
            if week:
                kwargs['week'] = week
            
            results = await asyncio.to_thread(
                self._rankings_api.get_rankings,
                **kwargs
            )
            
            if results:
                rankings = []
                for poll_week in results:
                    week_num = getattr(poll_week, 'week', None)
                    for poll in getattr(poll_week, 'polls', []):
                        poll_name = getattr(poll, 'poll', 'Unknown')
                        poll_ranks = []
                        for rank in getattr(poll, 'ranks', []):
                            poll_ranks.append({
                                'rank': getattr(rank, 'rank', None),
                                'school': getattr(rank, 'school', None),
                                'conference': getattr(rank, 'conference', None),
                                'firstPlaceVotes': getattr(rank, 'first_place_votes', None),
                                'points': getattr(rank, 'points', None),
                            })
                        rankings.append({
                            'week': week_num,
                            'poll': poll_name,
                            'ranks': poll_ranks
                        })
                logger.info(f"✅ Found {len(rankings)} poll(s)")
                return rankings
            return []
        except ApiException as e:
            logger.error(f"❌ Rankings API error: {e.status}")
            return []
        except Exception as e:
            logger.error(f"Error fetching rankings: {e}")
            return []

    async def get_team_ranking(self, team: str, year: int = 2025) -> Optional[Dict[str, Any]]:
        """Get a specific team's ranking across all polls"""
        rankings = await self.get_rankings(year)
        
        if not rankings:
            return None
        
        team_lower = team.lower()
        team_rankings = {}
        
        for poll in rankings:
            poll_name = poll.get('poll', 'Unknown')
            for rank in poll.get('ranks', []):
                if team_lower in rank.get('school', '').lower():
                    team_rankings[poll_name] = {
                        'rank': rank.get('rank'),
                        'points': rank.get('points'),
                        'firstPlaceVotes': rank.get('firstPlaceVotes'),
                    }
                    break
        
        if team_rankings:
            return {
                'team': team,
                'year': year,
                'rankings': team_rankings
            }
        return None

    async def get_matchup_history(self, team1: str, team2: str) -> Optional[Dict[str, Any]]:
        """Get historical matchup data between two teams"""
        if not self.is_available:
            return None

        try:
            logger.info(f"🔍 Fetching matchup history: {team1} vs {team2}")
            
            result = await asyncio.to_thread(
                self._teams_api.get_matchup,
                team1=team1,
                team2=team2
            )
            
            if result:
                games = []
                for game in getattr(result, 'games', []):
                    games.append({
                        'date': getattr(game, 'date', None),
                        'season': getattr(game, 'season', None),
                        'week': getattr(game, 'week', None),
                        'homeTeam': getattr(game, 'home_team', None),
                        'homeScore': getattr(game, 'home_score', None),
                        'awayTeam': getattr(game, 'away_team', None),
                        'awayScore': getattr(game, 'away_score', None),
                        'winner': getattr(game, 'winner', None),
                    })
                
                return {
                    'team1': getattr(result, 'team1', team1),
                    'team2': getattr(result, 'team2', team2),
                    'team1Wins': getattr(result, 'team1_wins', 0),
                    'team2Wins': getattr(result, 'team2_wins', 0),
                    'ties': getattr(result, 'ties', 0),
                    'games': games[-10:],  # Last 10 games
                }
            return None
        except ApiException as e:
            logger.error(f"❌ Matchup API error: {e.status}")
            return None
        except Exception as e:
            logger.error(f"Error fetching matchup: {e}")
            return None

    async def get_team_schedule(self, team: str, year: int = 2025) -> List[Dict[str, Any]]:
        """Get a team's schedule/results for a season"""
        if not self.is_available:
            return []

        try:
            logger.info(f"🔍 Fetching schedule for {team} ({year})")
            
            results = await asyncio.to_thread(
                self._games_api.get_games,
                year=year,
                team=team
            )
            
            if results:
                games = []
                for game in results:
                    games.append({
                        'week': getattr(game, 'week', None),
                        'date': getattr(game, 'start_date', None),
                        'homeTeam': getattr(game, 'home_team', None),
                        'homeScore': getattr(game, 'home_points', None),
                        'awayTeam': getattr(game, 'away_team', None),
                        'awayScore': getattr(game, 'away_points', None),
                        'venue': getattr(game, 'venue', None),
                        'completed': getattr(game, 'completed', False),
                    })
                logger.info(f"✅ Found {len(games)} games")
                return games
            return []
        except ApiException as e:
            logger.error(f"❌ Schedule API error: {e.status}")
            return []
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return []

    async def get_draft_picks(self, team: Optional[str] = None, year: int = 2025) -> List[Dict[str, Any]]:
        """Get NFL draft picks, optionally filtered by college team"""
        if not self.is_available:
            return []

        try:
            logger.info(f"🔍 Fetching draft picks" + (f" from {team}" if team else "") + f" ({year})")
            
            kwargs = {'year': year}
            if team:
                kwargs['college'] = team
            
            results = await asyncio.to_thread(
                self._draft_api.get_draft_picks,
                **kwargs
            )
            
            if results:
                picks = []
                for pick in results:
                    picks.append({
                        'round': getattr(pick, 'round', None),
                        'pick': getattr(pick, 'pick', None),
                        'overall': getattr(pick, 'overall', None),
                        'nflTeam': getattr(pick, 'nfl_team', None),
                        'name': getattr(pick, 'name', None),
                        'position': getattr(pick, 'position', None),
                        'college': getattr(pick, 'college_team', None),
                    })
                logger.info(f"✅ Found {len(picks)} draft picks")
                return picks
            return []
        except ApiException as e:
            logger.error(f"❌ Draft API error: {e.status}")
            return []
        except Exception as e:
            logger.error(f"Error fetching draft picks: {e}")
            return []

    async def get_team_transfers(self, team: str, year: int = 2025) -> Dict[str, List[Dict[str, Any]]]:
        """Get transfer portal activity for a team (incoming and outgoing)"""
        if not self.is_available:
            return {'incoming': [], 'outgoing': []}

        try:
            logger.info(f"🔍 Fetching transfers for {team} ({year})")
            
            results = await asyncio.to_thread(
                self._players_api.get_transfer_portal,
                year=year
            )
            
            incoming = []
            outgoing = []
            team_lower = team.lower()
            
            if results:
                for t in results:
                    transfer = {
                        'name': f"{getattr(t, 'first_name', '')} {getattr(t, 'last_name', '')}".strip(),
                        'position': getattr(t, 'position', None),
                        'origin': getattr(t, 'origin', None),
                        'destination': getattr(t, 'destination', None),
                        'stars': getattr(t, 'stars', None),
                        'rating': getattr(t, 'rating', None),
                        'eligibility': getattr(t, 'eligibility', None),
                    }
                    
                    origin = (getattr(t, 'origin', '') or '').lower()
                    dest = (getattr(t, 'destination', '') or '').lower()
                    
                    if team_lower in origin:
                        outgoing.append(transfer)
                    if team_lower in dest:
                        incoming.append(transfer)
            
            logger.info(f"✅ Found {len(incoming)} incoming, {len(outgoing)} outgoing transfers")
            return {'incoming': incoming, 'outgoing': outgoing}
        except ApiException as e:
            logger.error(f"❌ Transfer API error: {e.status}")
            return {'incoming': [], 'outgoing': []}
        except Exception as e:
            logger.error(f"Error fetching transfers: {e}")
            return {'incoming': [], 'outgoing': []}

    async def get_betting_lines(self, team: Optional[str] = None, year: int = 2025, week: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get betting lines for games"""
        if not self.is_available:
            return []

        try:
            logger.info(f"🔍 Fetching betting lines" + (f" for {team}" if team else "") + f" ({year})")
            
            kwargs = {'year': year}
            if team:
                kwargs['team'] = team
            if week:
                kwargs['week'] = week
            
            results = await asyncio.to_thread(
                self._betting_api.get_lines,
                **kwargs
            )
            
            if results:
                lines = []
                for game in results:
                    game_lines = []
                    for line in getattr(game, 'lines', []):
                        game_lines.append({
                            'provider': getattr(line, 'provider', None),
                            'spread': getattr(line, 'spread', None),
                            'overUnder': getattr(line, 'over_under', None),
                            'homeML': getattr(line, 'home_moneyline', None),
                            'awayML': getattr(line, 'away_moneyline', None),
                        })
                    
                    lines.append({
                        'homeTeam': getattr(game, 'home_team', None),
                        'homeScore': getattr(game, 'home_score', None),
                        'awayTeam': getattr(game, 'away_team', None),
                        'awayScore': getattr(game, 'away_score', None),
                        'week': getattr(game, 'week', None),
                        'lines': game_lines,
                    })
                logger.info(f"✅ Found {len(lines)} games with lines")
                return lines
            return []
        except ApiException as e:
            logger.error(f"❌ Betting API error: {e.status}")
            return []
        except Exception as e:
            logger.error(f"Error fetching betting lines: {e}")
            return []

    async def get_team_ratings(self, team: str, year: int = 2025) -> Optional[Dict[str, Any]]:
        """Get advanced ratings for a team (SP+, SRS, Elo, FPI)"""
        if not self.is_available:
            return None

        ratings = {}
        
        # SP+ Ratings
        try:
            sp_results = await asyncio.to_thread(
                self._ratings_api.get_sp,
                year=year,
                team=team
            )
            if sp_results:
                for r in sp_results:
                    ratings['sp'] = {
                        'rating': getattr(r, 'rating', None),
                        'ranking': getattr(r, 'ranking', None),
                        'offense': {
                            'rating': getattr(getattr(r, 'offense', None), 'rating', None) if hasattr(r, 'offense') else None,
                            'ranking': getattr(getattr(r, 'offense', None), 'ranking', None) if hasattr(r, 'offense') else None,
                        },
                        'defense': {
                            'rating': getattr(getattr(r, 'defense', None), 'rating', None) if hasattr(r, 'defense') else None,
                            'ranking': getattr(getattr(r, 'defense', None), 'ranking', None) if hasattr(r, 'defense') else None,
                        },
                    }
                    break
        except Exception as e:
            logger.warning(f"Could not fetch SP+ ratings: {e}")
        
        # SRS Ratings
        try:
            srs_results = await asyncio.to_thread(
                self._ratings_api.get_srs,
                year=year,
                team=team
            )
            if srs_results:
                for r in srs_results:
                    ratings['srs'] = {
                        'rating': getattr(r, 'rating', None),
                        'ranking': getattr(r, 'ranking', None),
                    }
                    break
        except Exception as e:
            logger.warning(f"Could not fetch SRS ratings: {e}")
        
        # Elo Ratings
        try:
            elo_results = await asyncio.to_thread(
                self._ratings_api.get_elo,
                year=year,
                team=team
            )
            if elo_results:
                for r in elo_results:
                    ratings['elo'] = {
                        'rating': getattr(r, 'elo', None),
                    }
                    break
        except Exception as e:
            logger.warning(f"Could not fetch Elo ratings: {e}")
        
        if ratings:
            logger.info(f"✅ Found ratings for {team}: {list(ratings.keys())}")
            return {
                'team': team,
                'year': year,
                'ratings': ratings
            }
        return None

    # ==================== FORMATTERS ====================

    def format_rankings(self, rankings: List[Dict], poll_filter: Optional[str] = None) -> str:
        """Format rankings for Discord"""
        if not rankings:
            return "No rankings available"
        
        response_parts = []
        
        for poll in rankings:
            poll_name = poll.get('poll', 'Unknown')
            if poll_filter and poll_filter.lower() not in poll_name.lower():
                continue
            
            response_parts.append(f"**{poll_name}**")
            for rank in poll.get('ranks', [])[:25]:  # Top 25
                r = rank.get('rank', '?')
                school = rank.get('school', 'Unknown')
                response_parts.append(f"{r}. {school}")
            response_parts.append("")
        
        return "\n".join(response_parts) if response_parts else "No matching polls found"

    def format_team_ranking(self, team_ranking: Dict) -> str:
        """Format a team's ranking across polls"""
        if not team_ranking:
            return "Team not ranked"
        
        team = team_ranking.get('team', 'Unknown')
        year = team_ranking.get('year', 2025)
        rankings = team_ranking.get('rankings', {})
        
        if not rankings:
            return f"**{team}** is not ranked in any major poll ({year})"
        
        parts = [f"📊 **{team}** Rankings ({year})"]
        for poll, data in rankings.items():
            rank = data.get('rank', '?')
            parts.append(f"• **{poll}:** #{rank}")
        
        return "\n".join(parts)

    def format_matchup(self, matchup: Dict) -> str:
        """Format matchup history for Discord"""
        if not matchup:
            return "No matchup data found"
        
        t1 = matchup.get('team1', 'Team 1')
        t2 = matchup.get('team2', 'Team 2')
        t1_wins = matchup.get('team1Wins', 0)
        t2_wins = matchup.get('team2Wins', 0)
        ties = matchup.get('ties', 0)
        
        parts = [
            f"🏈 **{t1} vs {t2}**",
            f"**All-Time Record:** {t1} leads {t1_wins}-{t2_wins}" + (f"-{ties}" if ties else ""),
            "",
            "**Recent Games:**"
        ]
        
        for game in matchup.get('games', [])[-5:]:  # Last 5
            season = game.get('season', '?')
            home = game.get('homeTeam', '?')
            away = game.get('awayTeam', '?')
            home_score = game.get('homeScore', '?')
            away_score = game.get('awayScore', '?')
            winner = game.get('winner', '')
            
            parts.append(f"• {season}: {away} {away_score} @ {home} {home_score}")
        
        return "\n".join(parts)

    def format_schedule(self, games: List[Dict], team: str) -> str:
        """Format team schedule for Discord"""
        if not games:
            return f"No schedule found for {team}"
        
        parts = [f"📅 **{team} Schedule**", ""]
        
        for game in games:
            week = game.get('week', '?')
            home = game.get('homeTeam', '?')
            away = game.get('awayTeam', '?')
            home_score = game.get('homeScore')
            away_score = game.get('awayScore')
            completed = game.get('completed', False)
            
            # Determine opponent and location
            is_home = team.lower() in home.lower()
            opponent = away if is_home else home
            location = "vs" if is_home else "@"
            
            if completed and home_score is not None:
                team_score = home_score if is_home else away_score
                opp_score = away_score if is_home else home_score
                result = "W" if (is_home and home_score > away_score) or (not is_home and away_score > home_score) else "L"
                parts.append(f"Wk {week}: {result} {location} {opponent} ({team_score}-{opp_score})")
            else:
                parts.append(f"Wk {week}: {location} {opponent}")
        
        return "\n".join(parts)

    def format_draft_picks(self, picks: List[Dict], team: Optional[str] = None) -> str:
        """Format draft picks for Discord"""
        if not picks:
            return f"No draft picks found" + (f" from {team}" if team else "")
        
        parts = [f"🏈 **NFL Draft Picks**" + (f" from {team}" if team else ""), ""]
        
        for pick in picks[:15]:  # Limit to 15
            rd = pick.get('round', '?')
            overall = pick.get('overall', '?')
            name = pick.get('name', 'Unknown')
            pos = pick.get('position', '?')
            nfl_team = pick.get('nflTeam', '?')
            college = pick.get('college', '')
            
            college_str = f" ({college})" if college and not team else ""
            parts.append(f"Rd {rd} (#{overall}): **{name}** {pos} → {nfl_team}{college_str}")
        
        return "\n".join(parts)

    def format_transfers(self, transfers: Dict, team: str) -> str:
        """Format transfer portal activity for Discord"""
        incoming = transfers.get('incoming', [])
        outgoing = transfers.get('outgoing', [])
        
        if not incoming and not outgoing:
            return f"No transfer portal activity found for {team}"
        
        parts = [f"🔄 **{team} Transfer Portal**", ""]
        
        if incoming:
            parts.append(f"**Incoming ({len(incoming)}):**")
            for t in incoming[:10]:
                name = t.get('name', 'Unknown')
                pos = t.get('position', '?')
                origin = t.get('origin', '?')
                stars = "⭐" * (t.get('stars') or 0)
                parts.append(f"• {name} ({pos}) from {origin} {stars}")
            parts.append("")
        
        if outgoing:
            parts.append(f"**Outgoing ({len(outgoing)}):**")
            for t in outgoing[:10]:
                name = t.get('name', 'Unknown')
                pos = t.get('position', '?')
                dest = t.get('destination') or 'TBD'
                parts.append(f"• {name} ({pos}) → {dest}")
        
        return "\n".join(parts)

    def format_betting_lines(self, lines: List[Dict]) -> str:
        """Format betting lines for Discord"""
        if not lines:
            return "No betting lines available"
        
        parts = ["💰 **Betting Lines**", ""]
        
        for game in lines[:10]:
            home = game.get('homeTeam', '?')
            away = game.get('awayTeam', '?')
            week = game.get('week', '?')
            
            # Get first available line
            game_lines = game.get('lines', [])
            if game_lines:
                line = game_lines[0]
                spread = line.get('spread')
                ou = line.get('overUnder')
                
                spread_str = f"{spread:+.1f}" if spread else "N/A"
                ou_str = f"O/U {ou}" if ou else ""
                
                parts.append(f"**{away} @ {home}** (Wk {week})")
                parts.append(f"   Spread: {home} {spread_str} | {ou_str}")
        
        return "\n".join(parts)

    def format_ratings(self, ratings: Dict) -> str:
        """Format advanced ratings for Discord"""
        if not ratings:
            return "No ratings available"
        
        team = ratings.get('team', 'Unknown')
        year = ratings.get('year', 2025)
        data = ratings.get('ratings', {})
        
        parts = [f"📈 **{team}** Advanced Ratings ({year})", ""]
        
        if 'sp' in data:
            sp = data['sp']
            parts.append(f"**SP+ Rating:** {sp.get('rating', 'N/A'):.1f}" if sp.get('rating') else "**SP+:** N/A")
            if sp.get('ranking'):
                parts.append(f"   Overall Rank: #{sp.get('ranking')}")
            if sp.get('offense', {}).get('ranking'):
                parts.append(f"   Offense Rank: #{sp['offense']['ranking']}")
            if sp.get('defense', {}).get('ranking'):
                parts.append(f"   Defense Rank: #{sp['defense']['ranking']}")
        
        if 'srs' in data:
            srs = data['srs']
            parts.append(f"**SRS:** {srs.get('rating', 'N/A'):.2f}" if srs.get('rating') else "")
        
        if 'elo' in data:
            elo = data['elo']
            parts.append(f"**Elo:** {elo.get('rating', 'N/A'):.0f}" if elo.get('rating') else "")
        
        return "\n".join(parts)

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

    def parse_cfb_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language CFB query and determine the type.
        
        Returns dict with:
        - 'type': One of 'player', 'rankings', 'matchup', 'schedule', 'draft', 
                  'transfers', 'betting', 'ratings', or None if not recognized
        - Additional fields depending on type
        """
        query = query.strip()
        
        # Remove Discord mentions
        query = re.sub(r'<@!?\d+>', '', query)
        query = query.strip()
        
        # Remove bot name prefix
        query_lower = query.lower()
        for prefix in ['harry', 'harry,', '@harry']:
            if query_lower.startswith(prefix):
                query = query[len(prefix):].strip()
                query_lower = query.lower()
        
        # Rankings patterns
        ranking_patterns = [
            r'(?:where is|what.s|how is)\s+(.+?)\s+ranked',
            r'(.+?)\s+(?:ranking|rankings?|rank)',
            r'(?:top 25|ap poll|coaches poll|cfp rankings?)',
            r'show me (?:the )?(?:top 25|rankings)',
        ]
        
        for pattern in ranking_patterns:
            match = re.search(pattern, query_lower)
            if match:
                team = match.group(1).strip() if match.lastindex else None
                return {'type': 'rankings', 'team': team.title() if team else None}
        
        # Matchup patterns (team vs team)
        matchup_patterns = [
            r'(.+?)\s+(?:vs?\.?|versus|against)\s+(.+?)(?:\s+(?:all.?time|history|record))?$',
            r'(?:history|record|matchup)\s+(?:between|of|for)\s+(.+?)\s+(?:vs?\.?|and|versus)\s+(.+?)$',
        ]
        
        for pattern in matchup_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'matchup',
                    'team1': match.group(1).strip().title(),
                    'team2': match.group(2).strip().rstrip('?.!').title()
                }
        
        # Schedule patterns
        schedule_patterns = [
            r'(?:when does|when do|when is)\s+(.+?)\s+play',
            r'(.+?)\s+(?:schedule|games?|next game)',
            r'(?:show me|get|what.s)\s+(.+?)\s+schedule',
        ]
        
        for pattern in schedule_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {'type': 'schedule', 'team': match.group(1).strip().title()}
        
        # Draft patterns
        draft_patterns = [
            r'(?:who got|who was|who.s been)\s+drafted\s+from\s+(.+)',
            r'(?:nfl )?draft\s+picks?\s+(?:from\s+)?(.+)',
            r'(.+?)\s+(?:nfl )?draft\s+picks?',
        ]
        
        for pattern in draft_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {'type': 'draft', 'team': match.group(1).strip().title()}
        
        # Transfer portal patterns
        transfer_patterns = [
            r'(?:who.s in|show me)\s+(?:the )?transfer portal\s+from\s+(.+)',
            r'(.+?)\s+transfer(?:s|\s+portal)',
            r'transfer portal\s+(?:for\s+)?(.+)',
        ]
        
        for pattern in transfer_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {'type': 'transfers', 'team': match.group(1).strip().title()}
        
        # Betting patterns
        betting_patterns = [
            r'(?:who.s favored|odds|spread|line|betting)\s+(?:for|in|on)?\s+(.+?)\s+(?:vs?\.?|versus|@|at)\s+(.+)',
            r'(.+?)\s+(?:vs?\.?|@)\s+(.+?)\s+(?:odds|spread|line)',
        ]
        
        for pattern in betting_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'betting',
                    'team1': match.group(1).strip().title(),
                    'team2': match.group(2).strip().rstrip('?.!').title()
                }
        
        # Ratings patterns (SP+, advanced stats)
        ratings_patterns = [
            r'(?:sp\+|srs|elo|fpi|rating)\s+(?:for\s+)?(.+)',
            r'(.+?)\s+(?:sp\+|srs|elo|advanced stats|ratings?)',
            r'how good is\s+(.+)',
        ]
        
        for pattern in ratings_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {'type': 'ratings', 'team': match.group(1).strip().title()}
        
        # Roster patterns
        roster_patterns = [
            r'(?:show me|get|what.s)\s+(.+?)(?:.s)?\s+roster',
            r'(.+?)\s+roster',
        ]
        
        for pattern in roster_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {'type': 'roster', 'team': match.group(1).strip().title()}
        
        # If no pattern matched but query mentions a team, might be a player query
        # Fall through to player query handling in bot.py
        return {'type': None}

    # ==================== BULK PLAYER LOOKUP ====================

    def parse_player_list(self, text: str) -> List[Dict[str, Optional[str]]]:
        """
        Parse a list of players in various formats.
        
        Supported formats:
        - James Smith (Bama DT)
        - Braden Atkinson (Mercer QB)
        - Vandrevius Jacobs (WR - Cocks)
        - Dre'Lon Miller (WR Colorado)
        - Isaiah Horton, Alabama, WR
        - James Smith from Alabama
        
        Returns list of dicts with 'name', 'team', 'position'
        """
        players = []
        
        # Split by newlines, commas at line level, or semicolons
        lines = re.split(r'[\n;]|(?:,\s*(?=[A-Z][a-z]+\s+[A-Z]))', text.strip())
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Remove bullet points, numbers, dashes at start
            line = re.sub(r'^[\-\*•\d\.\)]+\s*', '', line)
            
            player = {'name': None, 'team': None, 'position': None}
            
            # Pattern 1: Name (Team Position) or Name (Position - Team) or Name (Position Team)
            match = re.match(r'^([A-Za-z\'\-\s]+?)\s*\(([^)]+)\)\s*$', line)
            if match:
                player['name'] = match.group(1).strip()
                parens = match.group(2).strip()
                
                # Parse the parenthetical - could be "Bama DT", "DT - Cocks", "WR Colorado", etc.
                # Common positions
                positions = ['QB', 'RB', 'WR', 'TE', 'OL', 'OT', 'OG', 'C', 'DL', 'DT', 'DE', 'LB', 'CB', 'S', 'DB', 'K', 'P', 'LS', 'ATH']
                
                # Check for "Position - Team" or "Team Position" or "Position Team"
                for pos in positions:
                    if pos in parens.upper():
                        player['position'] = pos
                        # Remove position and delimiters to get team
                        team_part = re.sub(rf'\b{pos}\b', '', parens, flags=re.IGNORECASE)
                        team_part = re.sub(r'[\-\s]+', ' ', team_part).strip()
                        if team_part:
                            player['team'] = team_part
                        break
                else:
                    # No position found, assume it's all team
                    player['team'] = parens
                
                players.append(player)
                continue
            
            # Pattern 2: Name, Team, Position or Name from Team
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    player['name'] = parts[0]
                    player['team'] = parts[1]
                    if len(parts) >= 3:
                        player['position'] = parts[2].upper()
                    players.append(player)
                    continue
            
            # Pattern 3: Name from Team
            match = re.match(r'^([A-Za-z\'\-\s]+?)\s+(?:from|at|@)\s+(.+)$', line, re.IGNORECASE)
            if match:
                player['name'] = match.group(1).strip()
                player['team'] = match.group(2).strip()
                players.append(player)
                continue
            
            # Pattern 4: Just a name
            if re.match(r'^[A-Za-z\'\-\s]+$', line) and len(line.split()) >= 2:
                player['name'] = line.strip()
                players.append(player)
        
        # Clean up and title case
        for p in players:
            if p['name']:
                p['name'] = p['name'].title().strip()
            if p['team']:
                p['team'] = p['team'].title().strip()
        
        logger.info(f"✅ Parsed {len(players)} players from list")
        return players

    async def lookup_multiple_players(self, player_list: List[Dict[str, Optional[str]]]) -> List[Dict[str, Any]]:
        """
        Look up multiple players in parallel.
        
        Args:
            player_list: List of dicts with 'name' and optional 'team'
            
        Returns:
            List of results, each with 'query' (original) and 'result' (player info or None)
        """
        if not self.is_available:
            return []
        
        async def lookup_one(player_query: Dict) -> Dict[str, Any]:
            name = player_query.get('name')
            team = player_query.get('team')
            
            if not name:
                return {'query': player_query, 'result': None, 'error': 'No name provided'}
            
            try:
                result = await self.get_full_player_info(name, team)
                return {'query': player_query, 'result': result, 'error': None}
            except Exception as e:
                logger.error(f"Error looking up {name}: {e}")
                return {'query': player_query, 'result': None, 'error': str(e)}
        
        # Look up all players in parallel (but limit concurrency)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def lookup_with_limit(player_query):
            async with semaphore:
                return await lookup_one(player_query)
        
        tasks = [lookup_with_limit(p) for p in player_list]
        results = await asyncio.gather(*tasks)
        
        found = sum(1 for r in results if r.get('result'))
        logger.info(f"✅ Bulk lookup complete: {found}/{len(player_list)} players found")
        
        return results

    def format_bulk_player_response(self, results: List[Dict[str, Any]]) -> str:
        """Format bulk player lookup results for Discord"""
        if not results:
            return "No players to look up!"
        
        parts = []
        found_count = 0
        not_found = []
        
        for r in results:
            query = r.get('query', {})
            result = r.get('result')
            name = query.get('name', 'Unknown')
            team = query.get('team', '')
            
            if result:
                found_count += 1
                player = result.get('player', {})
                all_stats = result.get('all_stats', {})
                recruiting = result.get('recruiting')
                
                # Build compact player line
                p_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
                p_team = player.get('team', 'N/A')
                p_pos = player.get('position', '?')
                p_year = player.get('year', '')
                
                # Height/weight
                height = player.get('height')
                weight = player.get('weight')
                size = ""
                if height and height > 12:
                    feet = int(height) // 12
                    inches = int(height) % 12
                    size = f"{feet}'{inches}\""
                if weight:
                    size += f" {weight}lbs" if size else f"{weight}lbs"
                
                # Header line
                parts.append(f"**{p_name}** - {p_team} ({p_pos})")
                
                # Vitals line
                vitals = []
                if p_year:
                    vitals.append(p_year)
                if size:
                    vitals.append(size)
                if vitals:
                    parts.append(f"   {' | '.join(vitals)}")
                
                # Stats summary (most recent year only for bulk)
                if all_stats:
                    latest_year = max(all_stats.keys())
                    stats = all_stats[latest_year]
                    stat_line = self._format_compact_stats(stats, latest_year)
                    if stat_line:
                        parts.append(f"   {stat_line}")
                
                # Recruiting (compact)
                if recruiting:
                    stars = "⭐" * (recruiting.get('stars') or 0)
                    rating = recruiting.get('rating')
                    if stars or rating:
                        rec_line = f"   🎯 {stars}"
                        if rating:
                            rec_line += f" ({rating:.3f})"
                        parts.append(rec_line)
                
                parts.append("")  # Blank line between players
            else:
                not_found.append(f"{name}" + (f" ({team})" if team else ""))
        
        # Add not found section
        if not_found:
            parts.append("**❌ Not Found:**")
            for nf in not_found:
                parts.append(f"   • {nf}")
        
        # Summary
        summary = f"📊 **Found {found_count}/{len(results)} players**"
        
        return summary + "\n\n" + "\n".join(parts)

    def _format_compact_stats(self, stats: Dict, year: int) -> str:
        """Format stats compactly for bulk display"""
        stat_parts = []
        
        # Passing
        passing = stats.get('passing', {})
        if passing:
            yards = passing.get('YDS', passing.get('yards', 0))
            tds = passing.get('TD', passing.get('touchdowns', 0))
            if yards or tds:
                stat_parts.append(f"📊 {year}: {yards} pass yds, {tds} TD")
                return " | ".join(stat_parts)
        
        # Rushing
        rushing = stats.get('rushing', {})
        if rushing:
            yards = rushing.get('YDS', rushing.get('yards', 0))
            tds = rushing.get('TD', rushing.get('touchdowns', 0))
            if yards or tds:
                stat_parts.append(f"📊 {year}: {yards} rush yds, {tds} TD")
                return " | ".join(stat_parts)
        
        # Receiving
        receiving = stats.get('receiving', {})
        if receiving:
            rec = receiving.get('REC', receiving.get('receptions', 0))
            yards = receiving.get('YDS', receiving.get('yards', 0))
            tds = receiving.get('TD', receiving.get('touchdowns', 0))
            if rec or yards:
                stat_parts.append(f"📊 {year}: {rec} rec, {yards} yds, {tds} TD")
                return " | ".join(stat_parts)
        
        # Defense
        defense = stats.get('defense', {})
        if defense:
            tackles = defense.get('SOLO', 0) + defense.get('AST', 0)
            tfl = defense.get('TFL', 0)
            sacks = defense.get('SACKS', defense.get('SK', 0))
            if tackles or tfl or sacks:
                stat_parts.append(f"📊 {year}: {tackles} tkl, {tfl} TFL, {sacks} sacks")
                return " | ".join(stat_parts)
        
        return ""


# Backward compatibility alias
PlayerLookup = CFBDataLookup

# Singleton instance
player_lookup = CFBDataLookup()
cfb_data = player_lookup  # Alias for new features
