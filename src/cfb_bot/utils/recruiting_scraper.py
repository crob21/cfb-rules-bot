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
    # Player search - works well for finding players
    PLAYER_SEARCH_URL = "https://247sports.com/players/?&Player.Fullname={name}"
    SEASON_SEARCH_URL = "https://247sports.com/Season/{year}-Football/Recruits/?&Player.Fullname={name}"
    # Rankings pages
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
        Search for a recruit by name and scrape their full profile

        Args:
            name: Player name to search
            year: Recruiting class year (defaults to current)

        Returns:
            Recruit info dictionary with full profile data or None
        """
        if not year:
            year = self._get_current_recruiting_year()

        cache_key = f"recruit:{name.lower()}:{year}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Try year-specific search first
        urls_to_try = [
            self.SEASON_SEARCH_URL.format(year=year, name=quote_plus(name)),
        ]

        profile_url = None
        player_name = None

        for url in urls_to_try:
            html = await self._fetch_page(url)
            if not html:
                continue

            try:
                soup = BeautifulSoup(html, 'html.parser')

                # Find player links - look for /player/ URLs
                player_links = soup.select('a[href*="/player/"]')

                for link in player_links:
                    link_text = link.get_text(strip=True)
                    href = link.get('href', '')

                    # Skip non-player links (e.g., cbssports.com links)
                    if 'cbssports.com' in href or '/stats/player/' in href:
                        continue

                    # Check if this matches our search
                    if name.lower() in link_text.lower():
                        profile_url = href
                        player_name = link_text

                        # Fix URL - handle various formats
                        if profile_url.startswith('http'):
                            pass  # Already full URL
                        elif profile_url.startswith('//'):
                            # Protocol-relative URL (e.g., //247sports.com/player/...)
                            profile_url = 'https:' + profile_url
                        elif profile_url.startswith('/'):
                            profile_url = self.BASE_URL + profile_url
                        else:
                            profile_url = self.BASE_URL + '/' + profile_url

                        logger.info(f"✅ Found profile link: {player_name} -> {profile_url}")
                        break

                if profile_url:
                    break

            except Exception as e:
                logger.error(f"❌ Error parsing search results: {e}")
                continue

        # If direct search failed, try searching the composite rankings
        if not profile_url:
            logger.info(f"🔍 Direct search failed, trying composite rankings for {name}")
            profile_url, player_name = await self._search_composite_rankings(name, year)

        if not profile_url:
            logger.info(f"❌ No profile found for {name} ({year})")
            return None

        # Now fetch the full profile page
        recruit = await self._scrape_player_profile(profile_url, year)
        if recruit:
            self._set_cached(cache_key, recruit)

        return recruit

    async def _search_composite_rankings(self, name: str, year: int) -> tuple[Optional[str], Optional[str]]:
        """
        Search composite rankings page for a player (fallback when direct search fails)

        Args:
            name: Player name to search
            year: Recruiting class year

        Returns:
            Tuple of (profile_url, player_name) or (None, None)
        """
        # Try composite rankings page
        url = self.PLAYER_RANKINGS_URL.format(year=year)
        html = await self._fetch_page(url)

        if not html:
            return None, None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            name_lower = name.lower()
            name_parts = name_lower.split()

            # Find all player links
            player_links = soup.select('a[href*="/player/"]')

            for link in player_links:
                link_text = link.get_text(strip=True)
                href = link.get('href', '')

                # Skip non-player links
                if 'cbssports.com' in href or '/stats/player/' in href:
                    continue

                link_text_lower = link_text.lower()

                # Check for match - must match all parts of the name
                if all(part in link_text_lower for part in name_parts):
                    profile_url = href

                    # Fix URL format
                    if profile_url.startswith('//'):
                        profile_url = 'https:' + profile_url
                    elif profile_url.startswith('/'):
                        profile_url = self.BASE_URL + profile_url

                    logger.info(f"✅ Found via rankings: {link_text} -> {profile_url}")
                    return profile_url, link_text

            return None, None

        except Exception as e:
            logger.error(f"❌ Error searching composite rankings: {e}")
            return None, None

    async def _scrape_player_profile(self, profile_url: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Scrape a player's full 247Sports profile page

        Args:
            profile_url: Full URL to player profile
            year: Recruiting class year

        Returns:
            Detailed recruit data dictionary
        """
        html = await self._fetch_page(profile_url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            recruit = {
                'name': None,
                'year': year,
                'stars': None,
                'rating_247': None,
                'rating_composite': None,
                'national_rank': None,
                'national_rank_247': None,
                'position_rank': None,
                'position_rank_247': None,
                'state_rank': None,
                'state_rank_247': None,
                'position': None,
                'height': None,
                'weight': None,
                'city': None,
                'state': None,
                'high_school': None,
                'committed_to': None,
                'status': 'Uncommitted',
                'enrollment_date': None,
                'offers': [],
                'stats': [],
                'profile_url': profile_url,
                'scouting_report': None
            }

            # Player name - from h1 tag
            name_elem = soup.select_one('h1')
            if name_elem:
                recruit['name'] = name_elem.get_text(strip=True)

            # Position, Height, Weight from the player info section
            pos_elem = soup.select_one('li:has(span:contains("Pos")) span:last-child, .pos-height-weight .pos')
            if pos_elem:
                recruit['position'] = pos_elem.get_text(strip=True)

            height_elem = soup.select_one('li:has(span:contains("Height")) span:last-child, .pos-height-weight .height')
            if height_elem:
                recruit['height'] = height_elem.get_text(strip=True)

            weight_elem = soup.select_one('li:has(span:contains("Weight")) span:last-child, .pos-height-weight .weight')
            if weight_elem:
                recruit['weight'] = weight_elem.get_text(strip=True)

            # Try to get from page text if selectors don't work
            page_text = soup.get_text()

            # Extract position from "Pos QB" or similar
            if not recruit['position']:
                pos_match = re.search(r'Pos\s+([A-Z]{1,4})\b', page_text)
                if pos_match:
                    recruit['position'] = pos_match.group(1)

            # Extract height from "Height 6-3" or "6-3.5"
            if not recruit['height']:
                height_match = re.search(r'Height\s+([\d]+-[\d.]+)', page_text)
                if height_match:
                    recruit['height'] = height_match.group(1)

            # Extract weight
            if not recruit['weight']:
                weight_match = re.search(r'Weight\s+(\d{2,3})', page_text)
                if weight_match:
                    recruit['weight'] = weight_match.group(1)

            # High School and Location from Prospect Info
            school_elem = soup.select_one('.prospect-info li:has(span:contains("High School"))')
            if school_elem:
                recruit['high_school'] = school_elem.get_text(strip=True).replace('High School', '').strip()

            city_elem = soup.select_one('.prospect-info li:has(span:contains("City"))')
            if city_elem:
                city_text = city_elem.get_text(strip=True).replace('City', '').strip()
                if ', ' in city_text:
                    parts = city_text.split(', ')
                    recruit['city'] = parts[0]
                    recruit['state'] = parts[1][:2].upper() if len(parts) > 1 else None
                else:
                    recruit['city'] = city_text

            # Try from page text
            if not recruit['high_school']:
                hs_match = re.search(r'High School\s+([A-Za-z\s]+?)(?:\s+City|$)', page_text)
                if hs_match:
                    recruit['high_school'] = hs_match.group(1).strip()

            if not recruit['city'] or not recruit['state']:
                loc_match = re.search(r'City\s+([A-Za-z\s]+),\s+([A-Z]{2})', page_text)
                if loc_match:
                    recruit['city'] = loc_match.group(1).strip()
                    recruit['state'] = loc_match.group(2)

            # Class year
            class_match = re.search(r'Class\s+(\d{4})', page_text)
            if class_match:
                recruit['year'] = int(class_match.group(1))

            # Parse ratings and rankings from page text
            # Pattern: "247Sports      98      Natl.   3            QB  3    TN  1"
            # Pattern: "247Sports Composite®      0.9992      Natl.   1            QB  1    TN  1"

            # 247Sports Rating (the "98" number)
            rating_247_match = re.search(r'247Sports\s+(\d{2})\s+Natl', page_text)
            if rating_247_match:
                recruit['rating_247'] = int(rating_247_match.group(1))
                logger.debug(f"Found 247 rating: {recruit['rating_247']}")

            # 247Sports Composite Rating (0.9992)
            composite_match = re.search(r'Composite[®]?\s*(0\.\d{4}|1\.0000)', page_text)
            if composite_match:
                recruit['rating_composite'] = float(composite_match.group(1))
                logger.debug(f"Found composite: {recruit['rating_composite']}")

            # Rankings from 247Sports section (the "98" rating section)
            # Look for pattern: "98      Natl.   3            QB  3    TN  1"
            rank_section_match = re.search(r'247Sports\s+\d{2}\s+(Natl\.?\s*\d+.*?)(?:247Sports Composite|$)', page_text, re.DOTALL)
            if rank_section_match:
                rank_text = rank_section_match.group(1)

                # National rank
                natl_match = re.search(r'Natl\.?\s*(\d+)', rank_text)
                if natl_match:
                    recruit['national_rank_247'] = int(natl_match.group(1))

                # Position rank - look for position followed by number
                if recruit['position']:
                    pos_match = re.search(rf"{recruit['position']}\s+(\d+)", rank_text)
                    if pos_match:
                        recruit['position_rank_247'] = int(pos_match.group(1))

                # State rank - two letter state code followed by number
                # Need to exclude position codes (QB, WR, RB, etc.)
                position_codes = {'QB', 'WR', 'RB', 'TE', 'OL', 'OT', 'OG', 'DL', 'DT', 'DE', 'LB', 'CB', 'DB', 'WS', 'SS', 'FS', 'PK', 'PU', 'LS'}
                for match in re.finditer(r'\b([A-Z]{2})\s+(\d+)', rank_text):
                    code = match.group(1)
                    if code in self.STATES and code not in position_codes:
                        recruit['state'] = code
                        recruit['state_rank_247'] = int(match.group(2))
                        break

            # Composite rankings (from the composite section)
            comp_rank_match = re.search(r'Composite[®]?\s*[\d.]+\s+(Natl\.?\s*\d+.*?)(?:Your Prediction|Crystal Ball|$)', page_text, re.DOTALL)
            if comp_rank_match:
                comp_rank_text = comp_rank_match.group(1)

                natl_match = re.search(r'Natl\.?\s*(\d+)', comp_rank_text)
                if natl_match:
                    recruit['national_rank'] = int(natl_match.group(1))

                if recruit['position']:
                    pos_match = re.search(rf"{recruit['position']}\s+(\d+)", comp_rank_text)
                    if pos_match:
                        recruit['position_rank'] = int(pos_match.group(1))

                # State rank - exclude position codes
                position_codes = {'QB', 'WR', 'RB', 'TE', 'OL', 'OT', 'OG', 'DL', 'DT', 'DE', 'LB', 'CB', 'DB', 'WS', 'SS', 'FS', 'PK', 'PU', 'LS'}
                for match in re.finditer(r'\b([A-Z]{2})\s+(\d+)', comp_rank_text):
                    code = match.group(1)
                    if code in self.STATES and code not in position_codes:
                        recruit['state_rank'] = int(match.group(2))
                        break

            # If we didn't find composite national rank, use the 247 one
            if not recruit['national_rank'] and recruit['national_rank_247']:
                recruit['national_rank'] = recruit['national_rank_247']

            # Determine star rating from the 247 rating
            if recruit['rating_247']:
                if recruit['rating_247'] >= 98:
                    recruit['stars'] = 5
                elif recruit['rating_247'] >= 90:
                    recruit['stars'] = 4
                elif recruit['rating_247'] >= 80:
                    recruit['stars'] = 3
                elif recruit['rating_247'] >= 70:
                    recruit['stars'] = 2
                else:
                    recruit['stars'] = 1

            # Commitment status - check page text for patterns
            # Pattern: "Vanderbilt (NCAA)" or "Alabama Crimson Tide"
            # Look for school name patterns near player info

            # Check for "(NCAA)" pattern - indicates they're enrolled
            # Pattern: "Vanderbilt (NCAA)" in the player info
            ncaa_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\(NCAA\)', page_text)
            if ncaa_match:
                recruit['status'] = 'Enrolled'
                school_name = ncaa_match.group(1).strip()
                # Clean up the school name
                school_name = re.sub(r'^(NCAA|HS)\s*', '', school_name).strip()
                recruit['committed_to'] = school_name
                logger.debug(f"Found enrollment via (NCAA): {recruit['committed_to']}")

            # Also look for "Commodores Class FR" or similar (current class)
            if not recruit['committed_to']:
                team_class_match = re.search(r'(\w+)\s+Commodores|(\w+)\s+Crimson Tide|(\w+)\s+Bulldogs|(\w+)\s+Tigers|(\w+)\s+Ducks|(\w+)\s+Huskies|(\w+)\s+Gators|(\w+)\s+Buckeyes|(\w+)\s+Wolverines', page_text)
                if team_class_match:
                    # Get the first non-None group
                    for g in team_class_match.groups():
                        if g:
                            recruit['committed_to'] = g
                            recruit['status'] = 'Enrolled'
                            break

            # Look for explicit "Enrolled" or "Committed" text
            if 'Enrolled' in page_text:
                if not recruit['status']:
                    recruit['status'] = 'Enrolled'
                # Try to get enrollment date
                date_match = re.search(r'Enrolled\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{4})', page_text)
                if date_match:
                    recruit['enrollment_date'] = date_match.group(1)

            elif 'Committed' in page_text and not recruit['status']:
                recruit['status'] = 'Committed'

            # If we still don't have the school, look for college links
            if not recruit['committed_to']:
                school_links = soup.select('a[href*="/college/"]')
                for link in school_links:
                    school_name = link.get_text(strip=True)
                    # Filter out generic links
                    if school_name and len(school_name) > 2 and school_name not in ['NCAA', 'College']:
                        recruit['committed_to'] = school_name
                        if not recruit['status']:
                            recruit['status'] = 'Committed'
                        break

            # Parse stats table
            stats_table = soup.select_one('table')
            if stats_table:
                recruit['stats'] = self._parse_stats_table(stats_table)

            # Scouting report
            scout_elem = soup.select_one('.scouting-report, .evaluation')
            if scout_elem:
                recruit['scouting_report'] = scout_elem.get_text(strip=True)[:500]  # Truncate

            # Offers count
            offers_match = re.search(r'(\d+)\s+Offers?', page_text)
            if offers_match:
                recruit['offers_count'] = int(offers_match.group(1))

            logger.info(f"✅ Scraped profile: {recruit['name']} ({recruit['position']}) - {recruit['stars']}⭐")
            return recruit

        except Exception as e:
            logger.error(f"❌ Error parsing player profile: {e}", exc_info=True)
            return None

    def _parse_stats_table(self, table) -> List[Dict[str, Any]]:
        """Parse a stats table from 247Sports profile"""
        stats = []

        try:
            # Get headers
            headers = []
            header_row = table.select_one('thead tr, tr:first-child')
            if header_row:
                headers = [th.get_text(strip=True).lower() for th in header_row.select('th, td')]

            # Get data rows
            rows = table.select('tbody tr')

            for row in rows:
                cells = row.select('td')
                if not cells or len(cells) < 2:
                    continue

                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        key = headers[i]
                        value = cell.get_text(strip=True)
                        # Try to convert to int
                        try:
                            row_data[key] = int(value)
                        except ValueError:
                            row_data[key] = value

                if row_data:
                    stats.append(row_data)

        except Exception as e:
            logger.debug(f"Error parsing stats table: {e}")

        return stats

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
        star_display = '⭐' * stars if stars else ''
        position = recruit.get('position', '')
        year = recruit.get('year', '')

        lines.append(f"**{name}** {star_display}")
        if position:
            lines.append(f"📍 **{position}** | Class of **{year}**")
        lines.append("")

        # Ratings section
        lines.append("**📊 Ratings**")
        if recruit.get('rating_247'):
            lines.append(f"• 247Sports: **{recruit['rating_247']}**")
        if recruit.get('rating_composite'):
            lines.append(f"• Composite: **{recruit['rating_composite']:.4f}**")
        lines.append("")

        # Rankings section
        lines.append("**🏆 Rankings**")
        rank_lines = []

        # National
        natl = recruit.get('national_rank') or recruit.get('national_rank_247')
        if natl:
            rank_lines.append(f"• National: **#{natl}**")

        # Position
        pos_rank = recruit.get('position_rank') or recruit.get('position_rank_247')
        if pos_rank:
            rank_lines.append(f"• {position}: **#{pos_rank}**")

        # State
        state = recruit.get('state', '')
        state_rank = recruit.get('state_rank') or recruit.get('state_rank_247')
        if state_rank:
            rank_lines.append(f"• {state}: **#{state_rank}**")

        if rank_lines:
            lines.extend(rank_lines)
        else:
            lines.append("• _Rankings not available_")
        lines.append("")

        # Physical & Location
        lines.append("**📏 Profile**")
        physical = []
        if recruit.get('height'):
            physical.append(f"**{recruit['height']}**")
        if recruit.get('weight'):
            physical.append(f"**{recruit['weight']} lbs**")
        if physical:
            lines.append(f"• Size: {' / '.join(physical)}")

        if recruit.get('city') and recruit.get('state'):
            lines.append(f"• Hometown: {recruit['city']}, {recruit['state']}")
        if recruit.get('high_school'):
            lines.append(f"• High School: {recruit['high_school']}")

        if recruit.get('offers_count'):
            lines.append(f"• Offers: **{recruit['offers_count']}**")
        lines.append("")

        # Commitment status
        if recruit.get('committed_to'):
            status = recruit.get('status', 'Committed')
            lines.append(f"✅ **{status} to {recruit['committed_to']}**")
        else:
            lines.append("🔮 **Uncommitted**")

        # Stats (if available)
        stats = recruit.get('stats', [])
        if stats:
            lines.append("")
            lines.append("**📈 Career Stats**")

            # Show most recent year first
            for stat in stats[:3]:  # Show up to 3 seasons
                year_label = stat.get('year', 'Season')
                stat_parts = []

                # Passing stats
                if stat.get('paatt') or stat.get('pacmp'):
                    cmp = stat.get('pacmp', '?')
                    att = stat.get('paatt', '?')
                    yds = stat.get('payd', '?')
                    td = stat.get('patd', '?')
                    stat_parts.append(f"Pass: {cmp}/{att}, {yds}yd, {td}TD")

                # Rushing stats
                if stat.get('ruatt') or stat.get('ruyd'):
                    att = stat.get('ruatt', '?')
                    yds = stat.get('ruyd', '?')
                    td = stat.get('rutd', '?')
                    stat_parts.append(f"Rush: {att}car, {yds}yd, {td}TD")

                if stat_parts:
                    lines.append(f"**{year_label}**: {' | '.join(stat_parts)}")

        # Profile URL
        if recruit.get('profile_url'):
            lines.append("")
            lines.append(f"[View Full Profile on 247Sports]({recruit['profile_url']})")

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
