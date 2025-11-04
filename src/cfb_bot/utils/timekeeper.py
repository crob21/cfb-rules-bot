#!/usr/bin/env python3
"""
Timekeeper Module for CFB 26 League Bot
Manages advance countdown timers with notifications
Includes persistence to survive restarts/deployments
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
import discord

logger = logging.getLogger('CFB26Bot.Timekeeper')

# Timer state file location
TIMER_STATE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "timer_state.json"

class AdvanceTimer:
    """Manages advance countdown timers with custom durations"""

    def __init__(self, channel: discord.TextChannel, bot: discord.Client, manager=None):
        self.channel = channel
        self.bot = bot
        self.manager = manager  # Reference to TimekeeperManager for Discord persistence
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration_hours: int = 48
        self.is_active = False
        self.task: Optional[asyncio.Task] = None
        self.notifications_sent = {
            24: False,
            12: False,
            6: False,
            1: False
        }

    async def save_state(self):
        """Save timer state to disk, environment variable, and Discord for persistence"""
        if not self.is_active:
            # Clear saved state if timer is not active
            if TIMER_STATE_FILE.exists():
                TIMER_STATE_FILE.unlink()
            # Clear environment variable
            if 'TIMER_STATE' in os.environ:
                del os.environ['TIMER_STATE']
            # Clear Discord state
            if self.manager:
                await self.manager._save_state_to_discord({
                    'channel_id': self.channel.id,
                    'is_active': False
                })
            logger.info("💾 Cleared timer state (no active timer)")
            return

        try:
            state = {
                'channel_id': self.channel.id,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_hours': self.duration_hours,
                'is_active': self.is_active,
                'notifications_sent': self.notifications_sent
            }

            state_json = json.dumps(state)
            
            # Save to file (for local development)
            try:
                TIMER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(TIMER_STATE_FILE, 'w') as f:
                    json.dump(state, f, indent=2)
                logger.info(f"💾 Timer state saved to {TIMER_STATE_FILE}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save timer state to file: {e}")

            # Save to environment variable (for Render/Railway if manually set)
            try:
                os.environ['TIMER_STATE'] = state_json
                logger.debug("💾 Timer state saved to environment variable")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save timer state to environment variable: {e}")

            # Save to Discord (persists across deployments!)
            if self.manager:
                await self.manager._save_state_to_discord(state)
            
        except Exception as e:
            logger.error(f"❌ Failed to save timer state: {e}")

    async def start_countdown(self, hours: int = 48) -> bool:
        """Start a countdown with custom duration"""
        if self.is_active:
            logger.warning("⚠️ Countdown already active")
            return False

        self.start_time = datetime.now()
        self.duration_hours = hours
        self.end_time = self.start_time + timedelta(hours=hours)
        self.is_active = True
        self.notifications_sent = {24: False, 12: False, 6: False, 1: False}

        # Save state to disk, env var, and Discord
        await self.save_state()

        # Start the monitoring task
        self.task = asyncio.create_task(self._monitor_countdown())

        logger.info(f"⏰ Countdown started at {self.start_time}")
        logger.info(f"⏰ Duration: {hours} hours")
        logger.info(f"⏰ Countdown will end at {self.end_time}")
        return True

    async def stop_countdown(self) -> bool:
        """Stop the countdown"""
        if not self.is_active:
            return False

        self.is_active = False
        if self.task and not self.task.done():
            self.task.cancel()

        # Clear saved state
        await self.save_state()

        logger.info("⏹️ Countdown stopped")
        return True

    def get_time_remaining(self) -> Optional[timedelta]:
        """Get the time remaining on the countdown"""
        if not self.is_active or not self.end_time:
            return None

        remaining = self.end_time - datetime.now()
        if remaining.total_seconds() < 0:
            return timedelta(0)
        return remaining

    def get_status(self) -> Dict:
        """Get the current status of the countdown"""
        if not self.is_active:
            return {
                'active': False,
                'message': 'No countdown active'
            }

        remaining = self.get_time_remaining()
        if remaining is None:
            return {
                'active': False,
                'message': 'No countdown active'
            }

        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return {
            'active': True,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'remaining': remaining,
            'hours': hours,
            'minutes': minutes,
            'message': f'{hours}h {minutes}m remaining'
        }

    async def _monitor_countdown(self):
        """Monitor the countdown and send notifications"""
        try:
            while self.is_active:
                remaining = self.get_time_remaining()
                if remaining is None:
                    break

                total_hours = remaining.total_seconds() / 3600

                # Check for notification thresholds
                if total_hours <= 24 and not self.notifications_sent[24]:
                    await self._send_notification(24)
                    self.notifications_sent[24] = True
                    await self.save_state()  # Save after notification

                elif total_hours <= 12 and not self.notifications_sent[12]:
                    await self._send_notification(12)
                    self.notifications_sent[12] = True
                    await self.save_state()  # Save after notification

                elif total_hours <= 6 and not self.notifications_sent[6]:
                    await self._send_notification(6)
                    self.notifications_sent[6] = True
                    await self.save_state()  # Save after notification

                elif total_hours <= 1 and not self.notifications_sent[1]:
                    await self._send_notification(1)
                    self.notifications_sent[1] = True
                    await self.save_state()  # Save after notification

                # Check if time is up
                if total_hours <= 0:
                    await self._send_times_up()
                    self.is_active = False
                    await self.save_state()  # Clear state when timer ends
                    break

                # Check every minute
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("⏹️ Countdown monitoring task cancelled")
        except Exception as e:
            logger.error(f"❌ Error in countdown monitoring: {e}")

    async def _send_notification(self, hours: int):
        """Send a countdown notification"""
        embed = discord.Embed(
            title=f"⏰ {hours} Hour{'s' if hours > 1 else ''} Remaining!",
            description=f"Oi! Only **{hours} hour{'s' if hours > 1 else ''}** left until advance time, ya muppets!\n\nGet your bleedin' games played!",
            color=0xffa500
        )

        embed.set_footer(text=f"Harry's Advance Timer 🏈 | Ends at {self.end_time.strftime('%I:%M %p')}")

        try:
            await self.channel.send(embed=embed)
            logger.info(f"📢 Sent {hours}h notification")
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")

    async def _send_times_up(self):
        """Send the final TIMES UP message"""
        embed = discord.Embed(
            title="⏰ TIME'S UP! LET'S ADVANCE! ⏰",
            description="RIGHT THEN, TIME'S UP YA WANKERS!\n\n🏈 **LET'S ADVANCE THE BLOODY LEAGUE!** 🏈\n\nAll games should be done. If they ain't, tough luck mate!",
            color=0xff0000
        )

        embed.set_footer(text="Harry's Advance Timer 🏈")

        try:
            await self.channel.send(embed=embed)
            logger.info("📢 Sent TIMES UP message")
        except Exception as e:
            logger.error(f"❌ Failed to send times up message: {e}")


class TimekeeperManager:
    """Manages advance timers across multiple channels"""

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.timers: Dict[int, AdvanceTimer] = {}  # channel_id -> timer
        self.state_message_id: Optional[int] = None  # Discord message ID for state storage
        self.state_channel_id: Optional[int] = None  # Channel ID for state storage

    async def _save_state_to_discord(self, state: Dict):
        """Save timer state to a Discord channel message (persists across deployments)"""
        try:
            # Use the timer's channel or a default channel
            channel_id = state.get('channel_id')
            if not channel_id:
                return False
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False
            
            # Store state as JSON in message content
            state_json = json.dumps(state)
            
            # Try to find existing state message
            if self.state_message_id:
                try:
                    message = await channel.fetch_message(self.state_message_id)
                    await message.edit(content=f"```json\n{state_json}\n```")
                    logger.info("💾 Updated timer state message in Discord")
                    return True
                except discord.NotFound:
                    # Message was deleted, create new one
                    self.state_message_id = None
            
            # Create new state message (hidden from users)
            message = await channel.send(
                content=f"```json\n{state_json}\n```",
                silent=True  # Don't notify users
            )
            self.state_message_id = message.id
            self.state_channel_id = channel_id
            logger.info("💾 Created timer state message in Discord")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save timer state to Discord: {e}")
            return False

    async def _load_state_from_discord(self) -> Optional[Dict]:
        """Load timer state from Discord channel messages"""
        try:
            # Search for state messages in all channels the bot can access
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if not channel.permissions_for(guild.me).read_message_history:
                        continue
                    
                    # Search recent messages for state (look for JSON in code blocks)
                    try:
                        async for message in channel.history(limit=100):
                            if message.author == self.bot.user and message.content.startswith("```json"):
                                # Extract JSON from code block
                                content = message.content.strip()
                                if content.startswith("```json"):
                                    content = content[7:]  # Remove ```json
                                if content.endswith("```"):
                                    content = content[:-3]  # Remove ```
                                content = content.strip()
                                
                                try:
                                    state = json.loads(content)
                                    # Validate it's a timer state
                                    if 'channel_id' in state and 'end_time' in state:
                                        self.state_message_id = message.id
                                        self.state_channel_id = channel.id
                                        logger.info(f"📂 Found timer state message in #{channel.name}")
                                        return state
                                except json.JSONDecodeError:
                                    continue
                    except discord.Forbidden:
                        continue
                    except Exception as e:
                        logger.debug(f"Error searching channel {channel.name}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to load timer state from Discord: {e}")
            return None

    async def load_saved_state(self):
        """Load and restore any saved timer state from Discord, environment variable, or file"""
        state = None
        
        # Try loading from Discord first (most reliable for ephemeral file systems)
        state = await self._load_state_from_discord()
        if state:
            logger.info("📂 Loaded timer state from Discord")
        
        # Fallback to environment variable (for Render/Railway if manually set)
        if not state and 'TIMER_STATE' in os.environ:
            try:
                state_json = os.environ['TIMER_STATE']
                state = json.loads(state_json)
                logger.info("📂 Loaded timer state from environment variable")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load timer state from environment variable: {e}")
        
        # Fallback to file system (for local development)
        if not state and TIMER_STATE_FILE.exists():
            try:
                with open(TIMER_STATE_FILE, 'r') as f:
                    state = json.load(f)
                logger.info("📂 Loaded timer state from file")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load timer state from file: {e}")
        
        if not state:
            logger.info("📂 No saved timer state found")
            return

        try:

            channel_id = state.get('channel_id')
            if not channel_id:
                logger.warning("⚠️ Invalid timer state: no channel_id")
                return

            # Get the channel
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"⚠️ Could not find channel {channel_id}, clearing saved state")
                TIMER_STATE_FILE.unlink()
                return

            # Parse timestamps
            start_time = datetime.fromisoformat(state['start_time']) if state.get('start_time') else None
            end_time = datetime.fromisoformat(state['end_time']) if state.get('end_time') else None

            if not start_time or not end_time:
                logger.warning("⚠️ Invalid timer state: missing timestamps")
                return

            # Check if timer already expired
            if end_time < datetime.now():
                logger.info(f"⏰ Saved timer already expired, clearing state")
                # Clear file
                if TIMER_STATE_FILE.exists():
                    TIMER_STATE_FILE.unlink()
                # Clear Discord state
                await self._save_state_to_discord({
                    'channel_id': channel_id,
                    'is_active': False
                })
                return

            # Restore the timer
            timer = AdvanceTimer(channel, self.bot, manager=self)
            timer.start_time = start_time
            timer.end_time = end_time
            timer.duration_hours = state.get('duration_hours', 48)
            timer.is_active = True
            timer.notifications_sent = state.get('notifications_sent', {24: False, 12: False, 6: False, 1: False})

            # Start monitoring task
            timer.task = asyncio.create_task(timer._monitor_countdown())

            # Store in manager
            self.timers[channel_id] = timer

            time_remaining = end_time - datetime.now()
            hours_remaining = time_remaining.total_seconds() / 3600

            logger.info(f"✅ Restored timer for #{channel.name}")
            logger.info(f"⏰ Time remaining: {hours_remaining:.1f} hours")
            logger.info(f"⏰ End time: {end_time}")

            # Send a notification that timer was restored
            embed = discord.Embed(
                title="⏰ Timer Restored!",
                description=f"Right then! I've restored the advance countdown after a restart.\n\n**Time Remaining:** {int(hours_remaining)}h {int((time_remaining.total_seconds() % 3600) / 60)}m\n**Ends At:** {end_time.strftime('%I:%M %p')}",
                color=0x00ff00
            )
            embed.set_footer(text="Harry's Advance Timer 🏈 | Back online!")

            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"❌ Failed to send restoration message: {e}")

        except Exception as e:
            logger.error(f"❌ Failed to load timer state: {e}")
            # Clear corrupted state file
            if TIMER_STATE_FILE.exists():
                TIMER_STATE_FILE.unlink()
                logger.info("💾 Cleared corrupted timer state file")

    def get_timer(self, channel: discord.TextChannel) -> AdvanceTimer:
        """Get or create a timer for a channel"""
        if channel.id not in self.timers:
            self.timers[channel.id] = AdvanceTimer(channel, self.bot, manager=self)
        return self.timers[channel.id]

    async def start_timer(self, channel: discord.TextChannel, hours: int = 48) -> bool:
        """Start a timer for a channel with custom duration"""
        timer = self.get_timer(channel)
        return await timer.start_countdown(hours)

    async def stop_timer(self, channel: discord.TextChannel) -> bool:
        """Stop a timer for a channel"""
        if channel.id not in self.timers:
            return False
        return await self.timers[channel.id].stop_countdown()

    def get_status(self, channel: discord.TextChannel) -> Dict:
        """Get timer status for a channel"""
        if channel.id not in self.timers:
            return {
                'active': False,
                'message': 'No countdown active'
            }
        return self.timers[channel.id].get_status()
