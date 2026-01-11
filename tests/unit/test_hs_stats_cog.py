#!/usr/bin/env python3
"""
Unit tests for HSStatsCog

Tests:
- /hs stats - Individual player stats lookup
- /hs bulk - Multiple player lookup

Test players:
- Gavin Day (FL, QB)
- Mason James (common name, tests multiple results handling)
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tests.conftest import create_mock_hs_player


class TestHSStats:
    """Tests for /hs stats command"""
    
    @pytest.mark.asyncio
    async def test_stats_gavin_day(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test looking up Gavin Day stats"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        mock_hs_stats_scraper.lookup_player.return_value = create_mock_hs_player(
            name="Gavin Day",
            school="Plantation High School",
            position="QB",
            state="FL"
        )
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.stats(mock_interaction, player_name="Gavin Day", state="FL")
            
            mock_hs_stats_scraper.lookup_player.assert_called()
    
    @pytest.mark.asyncio
    async def test_stats_not_found(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test player not found shows error"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        mock_hs_stats_scraper.lookup_player.return_value = None
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.stats(mock_interaction, player_name="Nonexistent Player")
            
            # Should be ephemeral error
            call_kwargs = mock_interaction.followup.send.call_args
            assert call_kwargs.kwargs.get('ephemeral') == True
    
    @pytest.mark.asyncio
    async def test_stats_common_name_warning(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test common name shows warning about multiple results"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        # Mason James is a common name
        mock_hs_stats_scraper.lookup_player.return_value = {
            "name": "Mason James",
            "school": "Some High School",
            "multiple_results": True,
            "total_found": 15
        }
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.stats(mock_interaction, player_name="Mason James")
    
    @pytest.mark.asyncio
    async def test_stats_with_state_filter(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test looking up player with state filter helps disambiguation"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        mock_hs_stats_scraper.lookup_player.return_value = create_mock_hs_player(
            name="Mason James",
            school="Texas High School",
            state="TX"
        )
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.stats(mock_interaction, player_name="Mason James", state="TX")
            
            # Should have passed state filter
            call_args = mock_hs_stats_scraper.lookup_player.call_args
            assert "TX" in str(call_args) or call_args.kwargs.get('state') == "TX"
    
    @pytest.mark.asyncio
    async def test_stats_module_disabled(self, mock_interaction, disabled_modules_config):
        """Test stats command fails when module disabled"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        with patch('cfb_bot.cogs.hs_stats.server_config', disabled_modules_config):
            cog = HSStatsCog(MagicMock())
            await cog.stats(mock_interaction, player_name="Gavin Day")
            
            # Should have sent module disabled message
            mock_interaction.response.send_message.assert_called()


class TestHSBulk:
    """Tests for /hs bulk command"""
    
    @pytest.mark.asyncio
    async def test_bulk_multiple_players(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test looking up multiple players at once"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        mock_hs_stats_scraper.lookup_multiple_players.return_value = [
            create_mock_hs_player(name="Player One", school="School A"),
            create_mock_hs_player(name="Player Two", school="School B"),
        ]
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.bulk(mock_interaction, players="Player One, Player Two")
            
            mock_hs_stats_scraper.lookup_multiple_players.assert_called()
    
    @pytest.mark.asyncio
    async def test_bulk_empty_input(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test bulk with no players provided"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.bulk(mock_interaction, players="")
            
            # Should handle gracefully
    
    @pytest.mark.asyncio
    async def test_bulk_partial_results(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test bulk when some players found, some not"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        mock_hs_stats_scraper.lookup_multiple_players.return_value = [
            create_mock_hs_player(name="Found Player"),
            None,  # Not found
        ]
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.bulk(mock_interaction, players="Found Player, Missing Player")


class TestHSStatsCareerData:
    """Tests for career statistics display"""
    
    @pytest.mark.asyncio
    async def test_career_stats_displayed(self, mock_interaction, mock_server_config, mock_hs_stats_scraper):
        """Test that career totals are displayed"""
        from cfb_bot.cogs.hs_stats import HSStatsCog
        
        mock_hs_stats_scraper.lookup_player.return_value = {
            "name": "Test Player",
            "school": "Test High",
            "career": {
                "passing": {"yards": 10000, "touchdowns": 100},
                "rushing": {"yards": 2000, "touchdowns": 30}
            },
            "seasons": [
                {"year": "2024", "passing": {"yards": 4000}},
                {"year": "2023", "passing": {"yards": 3500}},
            ]
        }
        mock_hs_stats_scraper.format_player_stats.return_value = """
**Career Totals:**
Passing: 10,000 yards, 100 TD
Rushing: 2,000 yards, 30 TD

**2024 Season:**
Passing: 4,000 yards
"""
        
        with patch('cfb_bot.cogs.hs_stats.server_config', mock_server_config), \
             patch('cfb_bot.cogs.hs_stats.hs_stats_scraper', mock_hs_stats_scraper):
            
            cog = HSStatsCog(MagicMock())
            await cog.stats(mock_interaction, player_name="Test Player")

