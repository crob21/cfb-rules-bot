"""
High School Stats Scraper Module
Scrapes MaxPreps for high school football player stats.

⚠️ DISCLAIMER: Web scraping may violate MaxPreps Terms of Service.
This module is provided for educational/personal use only.
Use responsibly with appropriate rate limiting.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

logger = logging.getLogger('CFB26Bot.HSStats')

# Try to import scraping libraries
try:
    import httpx
    from bs4 import BeautifulSoup
    HS_SCRAPER_AVAILABLE = True
except ImportError:
    HS_SCRAPER_AVAILABLE = False
    logger.warning("⚠️ httpx or beautifulsoup4 not installed - HS stats scraper disabled")
    logger.warning("   Install with: pip install httpx beautifulsoup4")


class HSStatsScraper:
    """
    Scrapes MaxPreps for high school football player stats.
    
    Features:
    - Player search by name
    - State/school filtering for common names
    - Stats parsing (passing, rushing, receiving, defense)
    - Result caching (24hr TTL)
    - Rate limiting (1 req/sec)
    """
    
    BASE_URL = "https://www.maxpreps.com"
    SEARCH_URL = "https://www.maxpreps.com/search/default.aspx"
    
    # User agent to avoid blocks
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    # Rate limiting
    MIN_REQUEST_INTERVAL = 1.0  # seconds between requests
    
    # Cache settings
    CACHE_TTL = 24 * 60 * 60  # 24 hours in seconds
    
    def __init__(self):
        self.is_available = HS_SCRAPER_AVAILABLE
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time: float = 0
        self._client: Optional[httpx.AsyncClient] = None
        
        if not self.is_available:
            logger.warning("⚠️ HS Stats scraper not available - missing dependencies")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=30.0,
                follow_redirects=True
            )
        return self._client
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            await asyncio.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()
    
    def _get_cache_key(self, name: str, state: str = None, school: str = None) -> str:
        """Generate cache key for a player lookup"""
        key_parts = [name.lower().strip()]
        if state:
            key_parts.append(state.lower().strip())
        if school:
            key_parts.append(school.lower().strip())
        return ":".join(key_parts)
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if we have a valid cached result"""
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now().timestamp() - cached.get('timestamp', 0) < self.CACHE_TTL:
                logger.info(f"📦 Cache hit for {cache_key}")
                return cached.get('data')
        return None
    
    def _store_cache(self, cache_key: str, data: Dict[str, Any]):
        """Store result in cache"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
        
        # Clean old cache entries (keep last 100)
        if len(self._cache) > 100:
            oldest_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].get('timestamp', 0)
            )[:50]
            for key in oldest_keys:
                del self._cache[key]
    
    async def search_player(self, name: str, state: str = None) -> List[Dict[str, Any]]:
        """
        Search MaxPreps for a player by name.
        
        Args:
            name: Player name (e.g., "Arch Manning")
            state: Optional state to filter results (e.g., "Louisiana", "LA")
            
        Returns:
            List of matching player results with basic info
        """
        if not self.is_available:
            return []
        
        try:
            await self._rate_limit()
            client = await self._get_client()
            
            # Build search query
            search_query = name
            if state:
                search_query += f" {state}"
            
            # MaxPreps search URL format
            search_url = f"{self.BASE_URL}/search/athletes.aspx?search={quote_plus(search_query)}&sport=football"
            
            logger.info(f"🔍 Searching MaxPreps for: {search_query}")
            
            response = await client.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse search results
            results = []
            
            # MaxPreps search results are typically in a list/table format
            # The exact selectors may need adjustment based on current site structure
            player_cards = soup.select('.athlete-card, .search-result-item, .player-row, [data-athlete-id]')
            
            if not player_cards:
                # Try alternative selectors
                player_cards = soup.select('a[href*="/athlete/"]')
            
            for card in player_cards[:10]:  # Limit to top 10 results
                try:
                    # Extract player info
                    player_name = card.get_text(strip=True) if card.name == 'a' else card.select_one('.name, .athlete-name, h3, h4')
                    if player_name and hasattr(player_name, 'get_text'):
                        player_name = player_name.get_text(strip=True)
                    elif not isinstance(player_name, str):
                        player_name = str(player_name) if player_name else None
                    
                    # Get profile URL
                    profile_url = None
                    if card.name == 'a':
                        profile_url = card.get('href')
                    else:
                        link = card.select_one('a[href*="/athlete/"]')
                        if link:
                            profile_url = link.get('href')
                    
                    if profile_url and not profile_url.startswith('http'):
                        profile_url = self.BASE_URL + profile_url
                    
                    # Extract school/location info
                    school_elem = card.select_one('.school, .team-name, .location')
                    school = school_elem.get_text(strip=True) if school_elem else None
                    
                    if player_name and profile_url:
                        results.append({
                            'name': player_name,
                            'school': school,
                            'profile_url': profile_url
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"✅ Found {len(results)} search results for {name}")
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error searching MaxPreps: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error searching MaxPreps: {e}", exc_info=True)
            return []
    
    async def get_player_stats(self, profile_url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape stats from a player's MaxPreps profile page.
        
        Args:
            profile_url: Full URL to player's MaxPreps profile
            
        Returns:
            Dict with player info and stats
        """
        if not self.is_available:
            return None
        
        try:
            await self._rate_limit()
            client = await self._get_client()
            
            logger.info(f"🔍 Fetching stats from: {profile_url}")
            
            response = await client.get(profile_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract player info
            player_data = {
                'name': None,
                'school': None,
                'location': None,
                'position': None,
                'class_year': None,
                'height': None,
                'weight': None,
                'profile_url': profile_url,
                'seasons': []
            }
            
            # Player name
            name_elem = soup.select_one('h1, .athlete-name, .player-name')
            if name_elem:
                player_data['name'] = name_elem.get_text(strip=True)
            
            # School
            school_elem = soup.select_one('.school-name, .team-name, [data-school]')
            if school_elem:
                player_data['school'] = school_elem.get_text(strip=True)
            
            # Location (City, State)
            location_elem = soup.select_one('.location, .school-location')
            if location_elem:
                player_data['location'] = location_elem.get_text(strip=True)
            
            # Position
            pos_elem = soup.select_one('.position, [data-position]')
            if pos_elem:
                player_data['position'] = pos_elem.get_text(strip=True)
            
            # Parse stats tables
            stats_tables = soup.select('table.stats-table, table[data-sport="football"], .stats-container table')
            
            for table in stats_tables:
                season_stats = self._parse_stats_table(table)
                if season_stats:
                    player_data['seasons'].append(season_stats)
            
            # If no tables found, try alternative stat blocks
            if not player_data['seasons']:
                stat_blocks = soup.select('.stat-block, .career-stats, .season-stats')
                for block in stat_blocks:
                    stats = self._parse_stat_block(block)
                    if stats:
                        player_data['seasons'].append(stats)
            
            logger.info(f"✅ Scraped stats for {player_data.get('name', 'Unknown')}")
            return player_data
            
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error fetching stats: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching stats: {e}", exc_info=True)
            return None
    
    def _parse_stats_table(self, table) -> Optional[Dict[str, Any]]:
        """Parse a stats table into structured data"""
        try:
            stats = {
                'year': None,
                'games': None,
                'passing': {},
                'rushing': {},
                'receiving': {},
                'defense': {}
            }
            
            # Get headers
            headers = []
            header_row = table.select_one('thead tr, tr:first-child')
            if header_row:
                headers = [th.get_text(strip=True).lower() for th in header_row.select('th, td')]
            
            # Get data rows
            rows = table.select('tbody tr, tr:not(:first-child)')
            
            for row in rows:
                cells = row.select('td')
                if not cells:
                    continue
                
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text(strip=True)
                
                # Parse common stat fields
                if 'year' in row_data or 'season' in row_data:
                    stats['year'] = row_data.get('year') or row_data.get('season')
                
                if 'g' in row_data or 'games' in row_data:
                    stats['games'] = row_data.get('g') or row_data.get('games')
                
                # Passing stats
                if any(k in row_data for k in ['comp', 'att', 'pass yds', 'pass td']):
                    stats['passing'] = {
                        'completions': row_data.get('comp', row_data.get('cmp')),
                        'attempts': row_data.get('att'),
                        'yards': row_data.get('pass yds', row_data.get('yds')),
                        'touchdowns': row_data.get('pass td', row_data.get('td')),
                        'interceptions': row_data.get('int')
                    }
                
                # Rushing stats
                if any(k in row_data for k in ['rush', 'rush yds', 'rush td', 'car', 'carries']):
                    stats['rushing'] = {
                        'carries': row_data.get('car', row_data.get('carries', row_data.get('rush att'))),
                        'yards': row_data.get('rush yds', row_data.get('yds')),
                        'touchdowns': row_data.get('rush td', row_data.get('td')),
                        'avg': row_data.get('avg', row_data.get('ypc'))
                    }
                
                # Receiving stats
                if any(k in row_data for k in ['rec', 'receptions', 'rec yds', 'rec td']):
                    stats['receiving'] = {
                        'receptions': row_data.get('rec', row_data.get('receptions')),
                        'yards': row_data.get('rec yds', row_data.get('yds')),
                        'touchdowns': row_data.get('rec td', row_data.get('td')),
                        'avg': row_data.get('avg', row_data.get('ypr'))
                    }
                
                # Defense stats
                if any(k in row_data for k in ['tackles', 'tkl', 'sacks', 'int']):
                    stats['defense'] = {
                        'tackles': row_data.get('tackles', row_data.get('tkl')),
                        'sacks': row_data.get('sacks', row_data.get('sk')),
                        'interceptions': row_data.get('int'),
                        'forced_fumbles': row_data.get('ff')
                    }
            
            # Only return if we found some stats
            has_stats = (
                stats['passing'] or 
                stats['rushing'] or 
                stats['receiving'] or 
                stats['defense']
            )
            
            return stats if has_stats else None
            
        except Exception as e:
            logger.debug(f"Error parsing stats table: {e}")
            return None
    
    def _parse_stat_block(self, block) -> Optional[Dict[str, Any]]:
        """Parse a stat block (non-table format) into structured data"""
        try:
            text = block.get_text()
            stats = {
                'year': None,
                'passing': {},
                'rushing': {},
                'receiving': {},
                'defense': {}
            }
            
            # Try to extract stats using regex patterns
            # Passing: "150/250, 2500 YDS, 25 TD, 5 INT"
            pass_match = re.search(r'(\d+)[/-](\d+)[,\s]+(\d+)\s*(?:YDS|yards)[,\s]+(\d+)\s*TD', text, re.I)
            if pass_match:
                stats['passing'] = {
                    'completions': pass_match.group(1),
                    'attempts': pass_match.group(2),
                    'yards': pass_match.group(3),
                    'touchdowns': pass_match.group(4)
                }
            
            # Rushing: "150 CAR, 1200 YDS, 15 TD"
            rush_match = re.search(r'(\d+)\s*(?:CAR|carries)[,\s]+(\d+)\s*(?:YDS|yards)[,\s]+(\d+)\s*TD', text, re.I)
            if rush_match:
                stats['rushing'] = {
                    'carries': rush_match.group(1),
                    'yards': rush_match.group(2),
                    'touchdowns': rush_match.group(3)
                }
            
            # Receiving: "50 REC, 800 YDS, 10 TD"
            rec_match = re.search(r'(\d+)\s*(?:REC|receptions)[,\s]+(\d+)\s*(?:YDS|yards)[,\s]+(\d+)\s*TD', text, re.I)
            if rec_match:
                stats['receiving'] = {
                    'receptions': rec_match.group(1),
                    'yards': rec_match.group(2),
                    'touchdowns': rec_match.group(3)
                }
            
            has_stats = stats['passing'] or stats['rushing'] or stats['receiving']
            return stats if has_stats else None
            
        except Exception as e:
            logger.debug(f"Error parsing stat block: {e}")
            return None
    
    async def lookup_player(self, name: str, state: str = None, school: str = None) -> Optional[Dict[str, Any]]:
        """
        Complete player lookup: search + get stats.
        
        Args:
            name: Player name
            state: Optional state filter
            school: Optional school filter
            
        Returns:
            Dict with player info and stats, or None if not found
        """
        if not self.is_available:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(name, state, school)
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        # Search for player
        results = await self.search_player(name, state)
        
        if not results:
            logger.info(f"❌ No results found for {name}")
            return None
        
        # If school specified, try to match
        best_match = results[0]
        if school:
            school_lower = school.lower()
            for result in results:
                if result.get('school') and school_lower in result['school'].lower():
                    best_match = result
                    break
        
        # Get full stats
        profile_url = best_match.get('profile_url')
        if not profile_url:
            return None
        
        player_data = await self.get_player_stats(profile_url)
        
        if player_data:
            self._store_cache(cache_key, player_data)
        
        return player_data
    
    async def lookup_multiple_players(self, players: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Bulk player lookup.
        
        Args:
            players: List of dicts with 'name', optional 'state', optional 'school'
            
        Returns:
            List of player data dicts
        """
        if not self.is_available:
            return []
        
        results = []
        
        for player_info in players:
            name = player_info.get('name')
            if not name:
                continue
            
            try:
                data = await self.lookup_player(
                    name=name,
                    state=player_info.get('state'),
                    school=player_info.get('school')
                )
                
                results.append({
                    'query': player_info,
                    'found': data is not None,
                    'data': data
                })
                
            except Exception as e:
                logger.error(f"Error looking up {name}: {e}")
                results.append({
                    'query': player_info,
                    'found': False,
                    'error': str(e)
                })
        
        return results
    
    def format_player_stats(self, player_data: Dict[str, Any]) -> str:
        """Format player stats for Discord display"""
        if not player_data:
            return "No stats found"
        
        lines = []
        
        # Header
        name = player_data.get('name', 'Unknown Player')
        school = player_data.get('school', '')
        location = player_data.get('location', '')
        position = player_data.get('position', '')
        
        lines.append(f"🏈 **{name}**")
        if school:
            school_line = f"🏫 {school}"
            if location:
                school_line += f" ({location})"
            lines.append(school_line)
        if position:
            lines.append(f"📍 Position: {position}")
        
        lines.append("")
        
        # Stats by season
        seasons = player_data.get('seasons', [])
        if seasons:
            for season in seasons[-3:]:  # Show last 3 seasons
                year = season.get('year', 'Career')
                games = season.get('games', '')
                
                season_header = f"**{year}**"
                if games:
                    season_header += f" ({games} games)"
                lines.append(season_header)
                
                # Passing
                passing = season.get('passing', {})
                if passing and any(passing.values()):
                    comp = passing.get('completions', '?')
                    att = passing.get('attempts', '?')
                    yds = passing.get('yards', '?')
                    td = passing.get('touchdowns', '?')
                    int_val = passing.get('interceptions', '?')
                    lines.append(f"  🎯 Passing: {comp}/{att} | {yds} YDS | {td} TD | {int_val} INT")
                
                # Rushing
                rushing = season.get('rushing', {})
                if rushing and any(rushing.values()):
                    car = rushing.get('carries', '?')
                    yds = rushing.get('yards', '?')
                    td = rushing.get('touchdowns', '?')
                    lines.append(f"  🏃 Rushing: {car} CAR | {yds} YDS | {td} TD")
                
                # Receiving
                receiving = season.get('receiving', {})
                if receiving and any(receiving.values()):
                    rec = receiving.get('receptions', '?')
                    yds = receiving.get('yards', '?')
                    td = receiving.get('touchdowns', '?')
                    lines.append(f"  🙌 Receiving: {rec} REC | {yds} YDS | {td} TD")
                
                # Defense
                defense = season.get('defense', {})
                if defense and any(defense.values()):
                    tkl = defense.get('tackles', '?')
                    sacks = defense.get('sacks', '?')
                    ints = defense.get('interceptions', '?')
                    lines.append(f"  🛡️ Defense: {tkl} TKL | {sacks} SCK | {ints} INT")
                
                lines.append("")
        else:
            lines.append("_No stats available_")
        
        # Link to profile
        profile_url = player_data.get('profile_url')
        if profile_url:
            lines.append(f"[View Full Profile on MaxPreps]({profile_url})")
        
        return "\n".join(lines)
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()


# Global instance
hs_stats_scraper = HSStatsScraper()

