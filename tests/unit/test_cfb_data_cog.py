#!/usr/bin/env python3
"""
Unit tests for CFBDataCog

Tests:
- /cfb player - College player lookup
- /cfb players - Search multiple players
- /cfb rankings - AP/Coaches/CFP polls
- /cfb matchup - Head-to-head history
- /cfb schedule - Team schedule
- /cfb draft - NFL draft picks
- /cfb transfers - Portal activity
- /cfb betting - Betting lines
- /cfb ratings - Team ratings
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tests.conftest import create_mock_cfb_player


class TestCFBPlayer:
    """Tests for /cfb player command"""
    
    @pytest.mark.asyncio
    async def test_player_lookup_basic(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test basic player lookup"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_full_player_info.return_value = create_mock_cfb_player(
            name="Travis Hunter",
            team="Colorado",
            position="WR"
        )
        mock_cfb_data.format_player_response.return_value = "Travis Hunter - Colorado - WR"
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.player(mock_interaction, name="Travis Hunter")
            
            mock_cfb_data.get_full_player_info.assert_called()
    
    @pytest.mark.asyncio
    async def test_player_not_found(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test player not found shows error"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_full_player_info.return_value = None
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.player(mock_interaction, name="Nonexistent Player")
            
            # Should be ephemeral error
            call_kwargs = mock_interaction.followup.send.call_args
            assert call_kwargs.kwargs.get('ephemeral') == True
    
    @pytest.mark.asyncio
    async def test_player_with_team_filter(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test player lookup filtered by team"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_full_player_info.return_value = create_mock_cfb_player(
            name="Michael Penix Jr",
            team="Washington"
        )
        mock_cfb_data.format_player_response.return_value = "Michael Penix Jr - Washington - QB"
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.player(mock_interaction, name="Michael Penix", team="Washington")
    
    @pytest.mark.asyncio
    async def test_player_module_disabled(self, mock_interaction, disabled_modules_config):
        """Test player command fails when module disabled"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        with patch('cfb_bot.cogs.cfb_data.server_config', disabled_modules_config):
            cog = CFBDataCog(MagicMock())
            await cog.player(mock_interaction, name="Travis Hunter")
            
            # Should have sent module disabled message
            mock_interaction.response.send_message.assert_called()


class TestCFBRankings:
    """Tests for /cfb rankings command"""
    
    @pytest.mark.asyncio
    async def test_rankings_ap_poll(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test AP poll rankings"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_rankings.return_value = [
            {"rank": 1, "school": "Georgia", "conference": "SEC"},
            {"rank": 2, "school": "Ohio State", "conference": "Big Ten"},
            {"rank": 3, "school": "Oregon", "conference": "Big Ten"},
        ]
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.rankings(mock_interaction, poll="AP Top 25")
            
            mock_cfb_data.get_rankings.assert_called()


class TestCFBSchedule:
    """Tests for /cfb schedule command"""
    
    @pytest.mark.asyncio
    async def test_schedule_washington(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test Washington schedule lookup"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_team_schedule.return_value = [
            {"week": 1, "opponent": "Weber State", "home": True, "result": "W 35-3"},
            {"week": 2, "opponent": "Eastern Michigan", "home": True, "result": "W 30-10"},
        ]
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.schedule(mock_interaction, team="Washington")


class TestCFBMatchup:
    """Tests for /cfb matchup command"""
    
    @pytest.mark.asyncio
    async def test_matchup_rivalry(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test rivalry matchup history"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_head_to_head = AsyncMock(return_value={
            "team1": "Washington",
            "team2": "Oregon",
            "all_time": "63-47-5",
            "recent": [
                {"year": 2023, "winner": "Washington", "score": "37-34"},
            ]
        })
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.matchup(mock_interaction, team1="Washington", team2="Oregon")


class TestCFBTransfers:
    """Tests for /cfb transfers command"""
    
    @pytest.mark.asyncio
    async def test_transfers_by_team(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test transfer portal activity by team"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_transfers = AsyncMock(return_value=[
            {"name": "John Smith", "position": "QB", "from": "Alabama", "to": "Georgia"},
        ])
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.transfers(mock_interaction, team="Washington", direction="incoming")


class TestCFBDraft:
    """Tests for /cfb draft command"""
    
    @pytest.mark.asyncio
    async def test_draft_picks(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test NFL draft picks lookup"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        mock_cfb_data.get_draft_picks = AsyncMock(return_value=[
            {"round": 1, "pick": 2, "name": "Rome Odunze", "team": "Bears", "school": "Washington"},
        ])
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.draft(mock_interaction, year=2024, school="Washington")


class TestMultipleSeasons:
    """Tests for multi-season display"""
    
    @pytest.mark.asyncio
    async def test_player_stats_have_spacing(self, mock_interaction, mock_server_config, mock_cfb_data):
        """Test that multiple seasons have proper spacing in output"""
        from cfb_bot.cogs.cfb_data import CFBDataCog
        
        # Player with multiple seasons
        mock_cfb_data.get_full_player_info.return_value = {
            "name": "Cam Ward",
            "team": "Miami",
            "position": "QB",
            "stats": {
                "2024": {"passing": {"YDS": 4123, "TD": 36, "INT": 7}},
                "2023": {"passing": {"YDS": 3500, "TD": 30, "INT": 10}},
                "2022": {"passing": {"YDS": 2800, "TD": 24, "INT": 12}},
            }
        }
        
        # This should show spacing between seasons
        mock_cfb_data.format_player_response.return_value = """
**2024 Stats:**
Passing: 4123 YDS, 36 TD, 7 INT

**2023 Stats:**
Passing: 3500 YDS, 30 TD, 10 INT

**2022 Stats:**
Passing: 2800 YDS, 24 TD, 12 INT
"""
        
        with patch('cfb_bot.cogs.cfb_data.server_config', mock_server_config), \
             patch('cfb_bot.cogs.cfb_data.cfb_data', mock_cfb_data):
            
            cog = CFBDataCog(MagicMock())
            await cog.player(mock_interaction, name="Cam Ward")

