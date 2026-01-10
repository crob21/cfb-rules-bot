#!/usr/bin/env python3
"""
247Sports Recruiting Scraper

Scrapes recruiting data from 247Sports including:
- Player rankings and ratings
- Team recruiting class rankings
- Crystal Ball predictions
- Commitment tracking

Note: This uses web scraping since 247Sports has no public API.
Site structure changes may require updates to this module.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger('CFB26Bot.Recruiting')


class RecruitingScraper:
    """Scraper for 247Sports recruiting data"""

    BASE_URL = "https://247sports.com"
    SEARCH_URL = "https://247sports.com/Season/{year}-Football/Recruits/?&Player.Fullname={name}"
    PLAYER_RANKINGS_URL = "https://247sports.com/Season/{year}-Football/CompositeRecruitRankings/"
    TEAM_RANKINGS_URL = "https://247sports.com/Season/{year}-Football/CompositeTeamRankings/"
    POSITION_RANKINGS_URL = "https://247sports.com/Season/{year}-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool&Position={position}"
    STATE_RANKINGS_URL = "https://247sports.com/Season/{year}-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool&State={state}"

    # Position mapping
    POSITIONS = {
        'QB': 'QB', 'RB': 'RB', 'WR': 'WR', 'TE': 'TE',
        'OT': 'OT', 'OG': 'IOL', 'C': 'IOL', 'OL': 'OT',
        'EDGE': 'EDGE', 'DT': 'DL', 'DE': 'EDGE', 'DL': 'DL',
        'LB': 'LB', 'CB': 'CB', 'S': 'S', 'ATH': 'ATH'
    }

    # State abbreviations
    STATES = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
    }

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(hours=1)  # Cache for 1 hour
        self._last_request = datetime.min
        self._rate_limit_delay = 1.0  # 1 second between requests

        # HTTP client with browser-like headers
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _get_current_recruiting_year(self) -> int:
        """Get the current recruiting class year"""
        now = datetime.now()
        # Recruiting classes are for the following year until February
        if now.month >= 2:
            return now.year + 1
        return now.year

    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        now = datetime.now()
        elapsed = (now - self._last_request).total_seconds()
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request = datetime.now()

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return data
        return None

    def _set_cached(self, key: str, data: Any):
        """Cache data with timestamp"""
        self._cache[key] = (data, datetime.now())

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with rate limiting and error handling"""
        await self._rate_limit()

        try:
            logger.info(f"🔍 Fetching: {url}")
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self._headers)

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Page not found: {url}")
                    return None
                else:
                    logger.error(f"❌ HTTP {response.status_code} for {url}")
                    return None

        except httpx.TimeoutException:
            logger.error(f"❌ Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching {url}: {e}")
            return None

    def _parse_star_rating(self, element) -> Optional[int]:
        """Parse star rating from various element formats"""
        if not element:
            return None

        # Try to find star images or rating text
        text = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)

        # Look for number of stars
        if '★' in text:
            return text.count('★')

        # Look for numeric rating
        match = re.search(r'(\d+)\s*star', text.lower())
        if match:
            return int(match.group(1))

        # Check for star class
        star_class = element.get('class', []) if hasattr(element, 'get') else []
        for cls in star_class:
            if 'star' in cls.lower():
                match = re.search(r'(\d+)', cls)
                if match:
                    return int(match.group(1))

        return None

    def _parse_composite_rating(self, text: str) -> Optional[float]:
        """Parse composite rating (0.8000 - 1.0000)"""
        match = re.search(r'(0\.\d{4}|1\.0000)', text)
        if match:
            return float(match.group(1))
        return None

    async def search_recruit(self, name: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Search for a recruit by name

        Args:
            name: Player name to search
            year: Recruiting class year (defaults to current)

        Returns:
            Recruit info dictionary or None
        """
        if not year:
            year = self._get_current_recruiting_year()

        cache_key = f"recruit:{name.lower()}:{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = self.SEARCH_URL.format(year=year, name=quote_plus(name))
        html = await self._fetch_page(url)

        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find recruit rows in the table
            recruit_rows = soup.select('.rankings-page__list-item, .ri-page__list-item, tr.player')

            for row in recruit_rows:
                # Extract player name
                name_elem = row.select_one('.rankings-page__name-link, .ri-page__name-link, a.player')
                if not name_elem:
                    continue

                player_name = name_elem.get_text(strip=True)

                # Check if this is the player we're looking for
                if name.lower() not in player_name.lower():
                    continue

                # Parse recruit data
                recruit = self._parse_recruit_row(row, player_name)
                if recruit:
                    recruit['year'] = year
                    self._set_cached(cache_key, recruit)
                    logger.info(f"✅ Found recruit: {player_name}")
                    return recruit

            logger.info(f"❌ No results found for {name} ({year})")
            return None

        except Exception as e:
            logger.error(f"❌ Error parsing recruit search: {e}", exc_info=True)
            return None

    def _parse_recruit_row(self, row, player_name: str) -> Optional[Dict[str, Any]]:
        """Parse a recruit row from the rankings table"""
        try:
            recruit = {
                'name': player_name,
                'stars': None,
                'rating': None,
                'national_rank': None,
                'position_rank': None,
                'state_rank': None,
                'position': None,
                'height': None,
                'weight': None,
                'city': None,
                'state': None,
                'high_school': None,
                'committed_to': None,
                'status': 'Uncommitted'
            }

            # Try different selectors for the composite rating
            rating_elem = row.select_one('.score, .rating, .composite')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                recruit['rating'] = self._parse_composite_rating(rating_text)

            # Star rating
            star_elem = row.select_one('.rankings-page__star-and-score, .star-rating, .stars')
            if star_elem:
                recruit['stars'] = self._parse_star_rating(star_elem)

            # National rank
            rank_elem = row.select_one('.rank-column .primary, .rank, .natl')
            if rank_elem:
                rank_text = rank_elem.get_text(strip=True)
                match = re.search(r'(\d+)', rank_text)
                if match:
                    recruit['national_rank'] = int(match.group(1))

            # Position
            pos_elem = row.select_one('.position, .pos')
            if pos_elem:
                recruit['position'] = pos_elem.get_text(strip=True)

            # Location (city, state)
            location_elem = row.select_one('.location, .hometown, .meta')
            if location_elem:
                location = location_elem.get_text(strip=True)
                # Parse "City, ST" format
                parts = location.split(',')
                if len(parts) >= 2:
                    recruit['city'] = parts[0].strip()
                    recruit['state'] = parts[-1].strip()[:2].upper()

            # High school
            school_elem = row.select_one('.school, .high-school')
            if school_elem:
                recruit['high_school'] = school_elem.get_text(strip=True)

            # Commitment status
            commit_elem = row.select_one('.img-link img, .school-logo, .committed-to')
            if commit_elem:
                # Check for committed school
                alt_text = commit_elem.get('alt', '') if commit_elem.name == 'img' else ''
                title = commit_elem.get('title', '')
                if alt_text or title:
                    recruit['committed_to'] = alt_text or title
                    recruit['status'] = 'Committed'

            return recruit

        except Exception as e:
            logger.error(f"❌ Error parsing recruit row: {e}")
            return None

    async def get_top_recruits(
        self,
        year: Optional[int] = None,
        position: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Get top recruits with optional filters

        Args:
            year: Recruiting class year
            position: Filter by position (QB, WR, etc.)
            state: Filter by state (TX, CA, etc.)
            limit: Number of recruits to return

        Returns:
            List of recruit dictionaries
        """
        if not year:
            year = self._get_current_recruiting_year()

        # Determine which URL to use
        if position:
            pos_mapped = self.POSITIONS.get(position.upper(), position.upper())
            url = self.POSITION_RANKINGS_URL.format(year=year, position=pos_mapped)
            cache_key = f"top_recruits:{year}:pos:{pos_mapped}"
        elif state:
            state_upper = state.upper()
            url = self.STATE_RANKINGS_URL.format(year=year, state=state_upper)
            cache_key = f"top_recruits:{year}:state:{state_upper}"
        else:
            url = self.PLAYER_RANKINGS_URL.format(year=year)
            cache_key = f"top_recruits:{year}:all"

        cached = self._get_cached(cache_key)
        if cached:
            return cached[:limit]

        html = await self._fetch_page(url)
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            recruits = []

            # Find recruit rows
            rows = soup.select('.rankings-page__list-item, .ri-page__list-item')[:limit * 2]  # Get extra in case some fail

            for row in rows:
                if len(recruits) >= limit:
                    break

                name_elem = row.select_one('.rankings-page__name-link, .ri-page__name-link')
                if not name_elem:
                    continue

                player_name = name_elem.get_text(strip=True)
                recruit = self._parse_recruit_row(row, player_name)

                if recruit:
                    recruit['year'] = year
                    recruits.append(recruit)

            self._set_cached(cache_key, recruits)
            logger.info(f"✅ Found {len(recruits)} top recruits")
            return recruits[:limit]

        except Exception as e:
            logger.error(f"❌ Error parsing top recruits: {e}", exc_info=True)
            return []

    async def get_team_recruiting_class(
        self,
        team: str,
        year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a team's recruiting class

        Args:
            team: Team name
            year: Recruiting class year

        Returns:
            Team recruiting class info
        """
        if not year:
            year = self._get_current_recruiting_year()

        cache_key = f"team_class:{team.lower()}:{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # First get team rankings to find the team
        url = self.TEAM_RANKINGS_URL.format(year=year)
        html = await self._fetch_page(url)

        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find team rows
            team_rows = soup.select('.rankings-page__list-item, .team-rankings-item')

            for row in team_rows:
                # Get team name
                team_elem = row.select_one('.rankings-page__name-link, .team-name, a.team')
                if not team_elem:
                    continue

                team_name = team_elem.get_text(strip=True)

                # Check if this is the team we're looking for
                if team.lower() not in team_name.lower():
                    continue

                # Parse team data
                team_data = {
                    'team': team_name,
                    'year': year,
                    'rank': None,
                    'total_commits': None,
                    'avg_rating': None,
                    '5_stars': 0,
                    '4_stars': 0,
                    '3_stars': 0,
                    'points': None,
                    'commits': []
                }

                # Rank
                rank_elem = row.select_one('.rank-column .primary, .rank')
                if rank_elem:
                    match = re.search(r'(\d+)', rank_elem.get_text())
                    if match:
                        team_data['rank'] = int(match.group(1))

                # Total commits
                commits_elem = row.select_one('.total, .commits')
                if commits_elem:
                    match = re.search(r'(\d+)', commits_elem.get_text())
                    if match:
                        team_data['total_commits'] = int(match.group(1))

                # Average rating
                avg_elem = row.select_one('.avg, .average')
                if avg_elem:
                    rating = self._parse_composite_rating(avg_elem.get_text())
                    if rating:
                        team_data['avg_rating'] = rating

                # Points
                points_elem = row.select_one('.points, .score')
                if points_elem:
                    match = re.search(r'([\d.]+)', points_elem.get_text())
                    if match:
                        team_data['points'] = float(match.group(1))

                # Star counts - try to find breakdown
                star_elems = row.select('.star-breakdown span, .stars-count')
                for se in star_elems:
                    text = se.get_text(strip=True)
                    if '5' in text:
                        match = re.search(r'(\d+)', text)
                        if match:
                            team_data['5_stars'] = int(match.group(1))
                    elif '4' in text:
                        match = re.search(r'(\d+)', text)
                        if match:
                            team_data['4_stars'] = int(match.group(1))
                    elif '3' in text:
                        match = re.search(r'(\d+)', text)
                        if match:
                            team_data['3_stars'] = int(match.group(1))

                self._set_cached(cache_key, team_data)
                logger.info(f"✅ Found team class: {team_name} (Rank #{team_data['rank']})")
                return team_data

            logger.info(f"❌ Team not found: {team}")
            return None

        except Exception as e:
            logger.error(f"❌ Error parsing team class: {e}", exc_info=True)
            return None

    async def get_team_rankings(self, year: Optional[int] = None, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Get top team recruiting class rankings

        Args:
            year: Recruiting class year
            limit: Number of teams to return

        Returns:
            List of team recruiting class data
        """
        if not year:
            year = self._get_current_recruiting_year()

        cache_key = f"team_rankings:{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached[:limit]

        url = self.TEAM_RANKINGS_URL.format(year=year)
        html = await self._fetch_page(url)

        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            teams = []

            team_rows = soup.select('.rankings-page__list-item, .team-rankings-item')[:limit * 2]

            for row in team_rows:
                if len(teams) >= limit:
                    break

                team_elem = row.select_one('.rankings-page__name-link, .team-name')
                if not team_elem:
                    continue

                team_name = team_elem.get_text(strip=True)

                team_data = {
                    'team': team_name,
                    'year': year,
                    'rank': len(teams) + 1,  # Default to position in list
                    'total_commits': None,
                    'avg_rating': None,
                    'points': None
                }

                # Rank
                rank_elem = row.select_one('.rank-column .primary, .rank')
                if rank_elem:
                    match = re.search(r'(\d+)', rank_elem.get_text())
                    if match:
                        team_data['rank'] = int(match.group(1))

                # Total commits
                commits_elem = row.select_one('.total, .commits')
                if commits_elem:
                    match = re.search(r'(\d+)', commits_elem.get_text())
                    if match:
                        team_data['total_commits'] = int(match.group(1))

                # Points
                points_elem = row.select_one('.points, .score')
                if points_elem:
                    match = re.search(r'([\d.]+)', points_elem.get_text())
                    if match:
                        team_data['points'] = float(match.group(1))

                teams.append(team_data)

            self._set_cached(cache_key, teams)
            logger.info(f"✅ Found {len(teams)} team rankings")
            return teams[:limit]

        except Exception as e:
            logger.error(f"❌ Error parsing team rankings: {e}", exc_info=True)
            return []

    def format_recruit(self, recruit: Dict[str, Any]) -> str:
        """Format a single recruit for display"""
        if not recruit:
            return "❌ Recruit not found"

        lines = []

        # Name and basic info
        name = recruit.get('name', 'Unknown')
        stars = recruit.get('stars')
        star_display = '⭐' * stars if stars else '?'

        lines.append(f"**{name}** {star_display}")

        # Rankings
        rankings = []
        if recruit.get('national_rank'):
            rankings.append(f"#{recruit['national_rank']} National")
        if recruit.get('position_rank'):
            rankings.append(f"#{recruit['position_rank']} {recruit.get('position', 'Pos')}")
        if recruit.get('state_rank'):
            rankings.append(f"#{recruit['state_rank']} {recruit.get('state', 'State')}")

        if rankings:
            lines.append(' | '.join(rankings))

        # Rating
        if recruit.get('rating'):
            lines.append(f"📊 Rating: {recruit['rating']:.4f}")

        # Physical
        physical = []
        if recruit.get('height'):
            physical.append(recruit['height'])
        if recruit.get('weight'):
            physical.append(f"{recruit['weight']} lbs")
        if physical:
            lines.append(f"📏 {' / '.join(physical)}")

        # Location
        if recruit.get('city') and recruit.get('state'):
            lines.append(f"📍 {recruit['city']}, {recruit['state']}")
        if recruit.get('high_school'):
            lines.append(f"🏫 {recruit['high_school']}")

        # Commitment
        if recruit.get('committed_to'):
            lines.append(f"✅ **Committed to {recruit['committed_to']}**")
        else:
            lines.append("🔮 Uncommitted")

        return '\n'.join(lines)

    def format_team_class(self, team_data: Dict[str, Any]) -> str:
        """Format team recruiting class for display"""
        if not team_data:
            return "❌ Team not found"

        lines = []

        team = team_data.get('team', 'Unknown')
        rank = team_data.get('rank', '?')
        year = team_data.get('year', '')

        lines.append(f"**{team}** - #{rank} Nationally ({year})")
        lines.append("")

        # Stats
        if team_data.get('total_commits'):
            lines.append(f"👥 **{team_data['total_commits']}** Commits")

        if team_data.get('avg_rating'):
            lines.append(f"📊 Avg Rating: **{team_data['avg_rating']:.4f}**")

        if team_data.get('points'):
            lines.append(f"🏆 Points: **{team_data['points']:.2f}**")

        # Star breakdown
        stars = []
        if team_data.get('5_stars'):
            stars.append(f"⭐⭐⭐⭐⭐ {team_data['5_stars']}")
        if team_data.get('4_stars'):
            stars.append(f"⭐⭐⭐⭐ {team_data['4_stars']}")
        if team_data.get('3_stars'):
            stars.append(f"⭐⭐⭐ {team_data['3_stars']}")

        if stars:
            lines.append("")
            lines.append("**Star Breakdown:**")
            lines.extend(stars)

        return '\n'.join(lines)

    def format_top_recruits(self, recruits: List[Dict[str, Any]], title: str = "Top Recruits") -> str:
        """Format list of top recruits"""
        if not recruits:
            return "❌ No recruits found"

        lines = [f"**{title}**", ""]

        for i, r in enumerate(recruits, 1):
            stars = '⭐' * r.get('stars', 0) if r.get('stars') else ''
            name = r.get('name', 'Unknown')
            pos = r.get('position', '')
            commit = r.get('committed_to', '')

            if commit:
                lines.append(f"`{i:2d}.` {stars} **{name}** ({pos}) → {commit}")
            else:
                lines.append(f"`{i:2d}.` {stars} **{name}** ({pos})")

        return '\n'.join(lines)


# Global instance
recruiting_scraper = RecruitingScraper()
