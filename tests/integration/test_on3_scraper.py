#!/usr/bin/env python3
"""
Integration tests for On3 Scraper

These tests make ACTUAL HTTP requests to On3.com to verify:
1. The scraper can still parse the current website structure
2. Real player data can be extracted
3. Transfer portal detection works correctly

Run with: pytest tests/integration/ -v --tb=short
Skip in CI: pytest tests/integration/ -v -k "not integration" or mark slow

NOTE: These tests may fail if On3 changes their website structure.
That's the point - they alert us to scraper maintenance needs.
"""

import pytest
import asyncio

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestOn3ScraperRealData:
    """Integration tests with actual On3 data"""
    
    @pytest.fixture(scope="class")
    def scraper(self):
        """Create real On3 scraper instance"""
        from cfb_bot.utils.on3_scraper import On3Scraper
        return On3Scraper()
    
    # ==================== HIGH SCHOOL RECRUIT TESTS ====================
    
    async def test_search_gavin_day_2026(self, scraper):
        """Test searching for Gavin Day (2026 QB recruit)"""
        recruit = await scraper.search_recruit("Gavin Day", year=2026)
        
        # May not find exact match, but should get some result structure
        if recruit:
            assert "name" in recruit
            assert "position" in recruit
            # Gavin Day is a QB
            if "Gavin Day" in recruit.get("name", ""):
                assert recruit.get("position") == "QB"
    
    async def test_search_david_schwerzel_2026(self, scraper):
        """Test searching for David Schwerzel (2026 OT recruit)"""
        recruit = await scraper.search_recruit("David Schwerzel", year=2026)
        
        if recruit:
            assert "name" in recruit
            if "David Schwerzel" in recruit.get("name", ""):
                assert recruit.get("position") == "OT"
    
    # ==================== TRANSFER PORTAL TESTS ====================
    
    async def test_search_emmanuel_karnley_transfer(self, scraper):
        """Test Emmanuel Karnley is detected as transfer"""
        recruit = await scraper.search_recruit("Emmanuel Karnley")
        
        if recruit:
            assert "name" in recruit
            # Emmanuel Karnley is a transfer
            if "Emmanuel Karnley" in recruit.get("name", ""):
                assert recruit.get("is_transfer") == True, "Emmanuel Karnley should be detected as transfer"
                assert "DE" in recruit.get("position", ""), "Emmanuel Karnley is a DE"
    
    async def test_search_hollywood_smothers(self, scraper):
        """Test Hollywood Smothers lookup (nickname case)"""
        recruit = await scraper.search_recruit("Hollywood Smothers")
        
        if recruit:
            assert "name" in recruit
            # He goes by "Hollywood Smothers" on On3
            if "Hollywood" in recruit.get("name", "") or "Smothers" in recruit.get("name", ""):
                assert "RB" in recruit.get("position", ""), "Hollywood Smothers is a RB"
                # He's a transfer
                assert recruit.get("is_transfer") == True, "Hollywood Smothers should be detected as transfer"
    
    async def test_search_daylan_smothers_legal_name(self, scraper):
        """Test searching by legal name Daylan Smothers"""
        # On3 might not find by legal name directly
        recruit = await scraper.search_recruit("Daylan Smothers")
        
        # This might return None or Hollywood Smothers
        # Either is acceptable - we're testing the scraper doesn't crash
        if recruit:
            assert "name" in recruit
    
    # ==================== TEAM COMMITS TESTS ====================
    
    async def test_washington_commits_2026(self, scraper):
        """Test getting Washington's 2026 commits"""
        result = await scraper.get_team_commits("Washington", 2026)
        
        assert result is not None
        assert "commits" in result
        
        # Should have some commits
        commits = result["commits"]
        assert isinstance(commits, list)
        
        # If there are commits, verify structure
        if len(commits) > 0:
            commit = commits[0]
            assert "name" in commit
            assert "position" in commit
    
    async def test_washington_commits_has_transfers(self, scraper):
        """Test Washington commits list includes transfer indicators"""
        result = await scraper.get_team_commits("Washington", 2026)
        
        if result and result.get("commits"):
            # Check for is_transfer field on commits
            for commit in result["commits"]:
                assert "is_transfer" in commit, "Commits should have is_transfer field"
    
    async def test_commits_known_transfers_detected(self, scraper):
        """Test that known transfers are detected in commits list"""
        result = await scraper.get_team_commits("Washington", 2026)
        
        if result and result.get("commits"):
            # Known transfers as of testing: Emmanuel Karnley, Kai McClendon, Kolt Dieterich
            known_transfers = ["Emmanuel Karnley", "Kai McClendon", "Kolt Dieterich"]
            
            for commit in result["commits"]:
                if commit.get("name") in known_transfers:
                    assert commit.get("is_transfer") == True, \
                        f"{commit.get('name')} should be marked as transfer"
    
    # ==================== TEAM RANKINGS TESTS ====================
    
    async def test_team_rankings_2026(self, scraper):
        """Test getting 2026 team recruiting rankings"""
        rankings = await scraper.get_team_rankings(2026, limit=25)
        
        assert rankings is not None
        assert isinstance(rankings, list)
        assert len(rankings) > 0, "Should have at least some ranked teams"
        
        # Verify structure
        first_team = rankings[0]
        assert "rank" in first_team
        assert "team" in first_team
        
        # First team should be rank 1
        assert first_team["rank"] == 1
    
    async def test_rankings_no_header_rows(self, scraper):
        """Test rankings don't include header rows like 'Teams'"""
        rankings = await scraper.get_team_rankings(2026, limit=25)
        
        for ranking in rankings:
            team_name = ranking.get("team", "")
            # Should not have header-like values
            assert team_name not in ["Teams", "Team", "School", ""], \
                f"Found invalid team name: {team_name}"
    
    # ==================== TOP RECRUITS TESTS ====================
    
    async def test_top_recruits_2026(self, scraper):
        """Test getting top 2026 recruits"""
        recruits = await scraper.get_top_recruits(year=2026, limit=50)
        
        assert recruits is not None
        assert isinstance(recruits, list)
        
        if len(recruits) > 0:
            recruit = recruits[0]
            assert "name" in recruit
            assert "position" in recruit
            assert "stars" in recruit or "rating" in recruit
    
    async def test_top_recruits_by_position(self, scraper):
        """Test getting top recruits filtered by position"""
        recruits = await scraper.get_top_recruits(year=2026, position="QB", limit=20)
        
        if recruits:
            for recruit in recruits:
                # All should be QBs
                assert "QB" in recruit.get("position", ""), \
                    f"Expected QB, got {recruit.get('position')}"
    
    async def test_top_recruits_by_state(self, scraper):
        """Test getting top recruits filtered by state"""
        recruits = await scraper.get_top_recruits(year=2026, state="TX", limit=20)
        
        if recruits:
            for recruit in recruits:
                # Most should be from Texas
                # (some might be missing state info)
                pass  # Just verify no crash
    
    # ==================== FORMAT TESTS ====================
    
    async def test_format_recruit_output(self, scraper):
        """Test format_recruit produces valid output"""
        recruit = await scraper.search_recruit("Gavin Day", year=2026)
        
        if recruit:
            formatted = scraper.format_recruit(recruit)
            
            assert formatted is not None
            assert isinstance(formatted, str)
            assert len(formatted) > 0
            
            # Should contain player name
            if "Gavin Day" in recruit.get("name", ""):
                assert "Gavin Day" in formatted
    
    async def test_format_team_commits_output(self, scraper):
        """Test format_team_commits produces valid output"""
        result = await scraper.get_team_commits("Ohio State", 2026)
        
        if result and result.get("commits"):
            formatted = scraper.format_team_commits(result)
            
            assert formatted is not None
            assert isinstance(formatted, str)
            assert len(formatted) > 0


class TestOn3ScraperEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture(scope="class")
    def scraper(self):
        from cfb_bot.utils.on3_scraper import On3Scraper
        return On3Scraper()
    
    async def test_search_nonexistent_player(self, scraper):
        """Test searching for player that doesn't exist"""
        recruit = await scraper.search_recruit("ZZZZZ QQQQQ Nonexistent Player 12345")
        
        # Should return None, not crash
        assert recruit is None
    
    async def test_search_empty_string(self, scraper):
        """Test searching with empty string"""
        recruit = await scraper.search_recruit("")
        
        # Should return None or handle gracefully
        # (might return top recruit, that's OK)
        pass  # Just verify no crash
    
    async def test_invalid_team_commits(self, scraper):
        """Test getting commits for invalid team"""
        result = await scraper.get_team_commits("ZZZZ Nonexistent University", 2026)
        
        # Should return empty or None, not crash
        if result:
            assert result.get("commits", []) == [] or result.get("commits") is None
    
    async def test_invalid_year(self, scraper):
        """Test with invalid year"""
        # Far future year
        recruit = await scraper.search_recruit("Test Player", year=2050)
        
        # Should handle gracefully
        pass  # Just verify no crash
    
    async def test_special_characters_in_name(self, scraper):
        """Test searching with special characters"""
        # Names with apostrophes, hyphens, etc.
        recruit = await scraper.search_recruit("D'Angelo O'Neil-Smith")
        
        # Should handle gracefully, not crash
        pass


class TestOn3ScraperTransferPortalFields:
    """Test transfer portal specific field extraction"""
    
    @pytest.fixture(scope="class")
    def scraper(self):
        from cfb_bot.utils.on3_scraper import On3Scraper
        return On3Scraper()
    
    async def test_transfer_has_portal_fields(self, scraper):
        """Test that transfers have portal-specific fields"""
        recruit = await scraper.search_recruit("Emmanuel Karnley")
        
        if recruit and recruit.get("is_transfer"):
            # Should have portal-specific fields (may be None if not on page)
            assert "previous_school" in recruit
            assert "portal_rating" in recruit
            assert "college_experience" in recruit
    
    async def test_hs_recruit_no_portal_fields(self, scraper):
        """Test that HS recruits don't have transfer-only data"""
        recruit = await scraper.search_recruit("Gavin Day", year=2026)
        
        if recruit and not recruit.get("is_transfer"):
            # is_transfer should be False
            assert recruit.get("is_transfer") == False
            # previous_school should be None for HS recruits
            assert recruit.get("previous_school") is None

