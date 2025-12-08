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
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    # Fallback for older Python versions
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        ZoneInfo = None

logger = logging.getLogger('CFB26Bot.Timekeeper')

# EST/EDT timezone (America/New_York handles DST automatically)
EST_TIMEZONE = ZoneInfo('America/New_York') if ZoneInfo else None

def to_est(dt: datetime) -> datetime:
    """Convert a datetime to EST/EDT"""
    if not dt:
        return dt
    if EST_TIMEZONE and ZoneInfo:
        # If datetime is naive, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        # Convert to EST
        return dt.astimezone(EST_TIMEZONE)
    return dt  # Fallback if timezone not available

def format_est_time(dt: datetime, format_str: str = '%I:%M %p on %B %d') -> str:
    """Format a datetime in EST/EDT"""
    if not dt:
        return "N/A"
    est_dt = to_est(dt)
    if EST_TIMEZONE:
        return est_dt.strftime(format_str) + ' EST/EDT'
    return est_dt.strftime(format_str)

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
            # This MUST succeed for persistence to work
            if self.manager:
                discord_saved = await self.manager._save_state_to_discord(state)
                if not discord_saved:
                    logger.error("❌ CRITICAL: Failed to save timer state to Discord - timer will NOT persist!")
                else:
                    logger.info("✅ Timer state saved to Discord successfully")
            else:
                logger.error("❌ CRITICAL: No manager available - timer state NOT saved to Discord!")

        except Exception as e:
            logger.error(f"❌ Failed to save timer state: {e}")
            logger.exception("Full error details:")

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

        embed.set_footer(text=f"Harry's Advance Timer 🏈 | Ends at {format_est_time(self.end_time, '%I:%M %p')}")

        try:
            await self.channel.send(embed=embed)
            logger.info(f"📢 Sent {hours}h notification")
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")

    async def _send_times_up(self):
        """Send the final TIMES UP message"""
        # Get season/week info for display
        season_info = None
        if self.manager:
            season_info = self.manager.get_season_week()
            # Increment the week when advance completes
            if season_info['season'] and season_info['week'] is not None:
                await self.manager.increment_week()
                logger.info(f"📅 Week incremented from {season_info['week']} to {season_info['week'] + 1}")
        
        # Build description with season/week if available
        description = "RIGHT THEN, TIME'S UP YA WANKERS!\n\n🏈 **LET'S ADVANCE THE BLOODY LEAGUE!** 🏈\n\n"
        if season_info and season_info['season'] and season_info['week'] is not None:
            new_week = season_info['week'] + 1
            description += f"**Season {season_info['season']}, Week {season_info['week']}** → **Week {new_week}**\n\n"
        description += "All games should be done. If they ain't, tough luck mate!"
        
        embed = discord.Embed(
            title="⏰ TIME'S UP! LET'S ADVANCE! ⏰",
            description=description,
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
        self.season: Optional[int] = None  # Current season number
        self.week: Optional[int] = None  # Current week number

    async def _save_state_to_discord(self, state: Dict):
        """Save timer state to a Discord DM channel (persists across deployments, invisible to users)"""
        try:
            # Try to get bot owner for DM channel (more private)
            bot_owner_id = None
            try:
                app_info = await self.bot.application_info()
                bot_owner_id = app_info.owner.id if app_info.owner else None
            except Exception as e:
                logger.debug(f"Could not get application info: {e}")
                pass

            # If we have bot owner, use DM channel (invisible to users)
            if bot_owner_id:
                try:
                    bot_owner = await self.bot.fetch_user(bot_owner_id)
                    # Try to get existing DM channel first
                    dm_channel = bot_owner.dm_channel
                    if not dm_channel:
                        # Try to create DM channel (may fail if user hasn't interacted with bot)
                        dm_channel = await bot_owner.create_dm()

                    # Store state as JSON
                    state_json = json.dumps(state)

                    # Try to find existing state message in DM
                    if self.state_message_id:
                        try:
                            message = await dm_channel.fetch_message(self.state_message_id)
                            await message.edit(content=f"```json\n{state_json}\n```")
                            logger.info("💾 Updated timer state message in bot owner DM")
                            return True
                        except discord.NotFound:
                            self.state_message_id = None

                    # Clean up old state messages
                    try:
                        async for message in dm_channel.history(limit=10):
                            if (message.author == self.bot.user and
                                message.content.startswith("```json") and
                                "channel_id" in message.content):
                                if message.id != self.state_message_id:
                                    try:
                                        await message.delete()
                                    except:
                                        pass
                    except:
                        pass

                    # Create new state message in DM (invisible to users!)
                    message = await dm_channel.send(content=f"```json\n{state_json}\n```")
                    self.state_message_id = message.id
                    logger.info("💾 Created timer state message in bot owner DM (invisible to users)")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Could not use DM channel for state storage: {e}, falling back to timer channel")
                    logger.debug("DM channel error details", exc_info=True)
                    # Continue to fallback below

            # Fallback: Use timer's channel (visible but necessary)
            channel_id = state.get('channel_id')
            if not channel_id:
                logger.error("❌ No channel_id in state - cannot save to Discord")
                return False

            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"❌ Channel {channel_id} not found - cannot save state")
                return False

            # Store state as JSON in message content
            state_json = json.dumps(state)

            # Try to find existing state message and update it
            if self.state_message_id:
                try:
                    message = await channel.fetch_message(self.state_message_id)
                    # Update existing message (edit is less visible than new message)
                    await message.edit(content=f"```json\n{state_json}\n```")
                    logger.info("💾 Updated timer state message in Discord channel")
                    return True
                except discord.NotFound:
                    # Message was deleted, create new one
                    logger.debug("State message not found, will create new one")
                    self.state_message_id = None
                except Exception as e:
                    logger.warning(f"⚠️ Failed to update state message: {e}, will create new one")
                    self.state_message_id = None

            # Clean up old state messages from this bot to avoid clutter
            try:
                async for message in channel.history(limit=50):
                    if (message.author == self.bot.user and
                        message.content.startswith("```json") and
                        "channel_id" in message.content and
                        "end_time" in message.content and
                        message.id != self.state_message_id):  # Don't delete the one we're tracking
                        # Delete old state messages to keep channel clean
                        try:
                            await message.delete()
                            logger.debug(f"🗑️ Deleted old timer state message")
                        except:
                            pass  # Ignore if we can't delete
            except Exception as e:
                logger.debug(f"Could not clean up old messages: {e}")

            # Create new state message (silent, but still visible)
            try:
                message = await channel.send(
                    content=f"```json\n{state_json}\n```",
                    silent=True  # Don't notify users (but message still visible)
                )
                self.state_message_id = message.id
                self.state_channel_id = channel_id
                logger.info(f"💾 Created timer state message in #{channel.name} (fallback - visible to users)")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to create state message in channel: {e}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to save timer state to Discord: {e}")
            logger.exception("Full error details:")
            return False

    async def _load_state_from_discord(self) -> Optional[Dict]:
        """Load timer state from Discord (DM channel first, then public channels)"""
        try:
            # First, try to get state from bot owner's DM channel (preferred, invisible)
            logger.info("🔍 Checking bot owner DM channel for timer state...")
            try:
                app_info = await self.bot.application_info()
                bot_owner_id = app_info.owner.id if app_info.owner else None

                if bot_owner_id:
                    logger.info(f"📧 Bot owner ID: {bot_owner_id}")
                    try:
                        bot_owner = await self.bot.fetch_user(bot_owner_id)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not fetch bot owner: {e}")
                        raise  # Will fall back to public channels

                    try:
                        dm_channel = bot_owner.dm_channel
                        if not dm_channel:
                            # Try to create DM channel (may fail if user hasn't interacted with bot)
                            dm_channel = await bot_owner.create_dm()
                    except Exception as e:
                        logger.warning(f"⚠️ Could not create/access DM channel: {e}")
                        logger.info("💡 Tip: Bot owner needs to have DMs enabled - falling back to public channels")
                        raise  # Will fall back to public channels

                    logger.info(f"📧 DM channel created/accessed: {dm_channel.id}")

                    # Search DM channel for state messages
                    message_count = 0
                    async for message in dm_channel.history(limit=10):
                        message_count += 1
                        if message.author == self.bot.user and message.content.startswith("```json"):
                            logger.info(f"📧 Found JSON message in DM (message #{message_count})")
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
                                    logger.info(f"✅ Found timer state message in bot owner DM")
                                    return state
                            except json.JSONDecodeError as e:
                                logger.debug(f"Failed to parse JSON from DM message: {e}")
                                continue
                    logger.info(f"📧 Searched {message_count} messages in DM, no timer state found")
                    # If we got here, DM worked but no state found - continue to public channels
                else:
                    logger.warning("⚠️ Could not get bot owner ID")
            except Exception as e:
                logger.warning(f"⚠️ Could not check DM channel: {e}")
                logger.debug("Full error details", exc_info=True)
                # Continue to fallback - public channels

            # Fallback: Search for state messages in all channels the bot can access
            logger.info("🔍 Checking public channels for timer state...")
            channels_checked = 0
            messages_checked = 0
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if not channel.permissions_for(guild.me).read_message_history:
                        continue

                    channels_checked += 1

                    # Search recent messages for state (look for JSON in code blocks)
                    try:
                        async for message in channel.history(limit=100):
                            messages_checked += 1
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
                                        # Found state in public channel - migrate to DM and delete this one
                                        self.state_message_id = message.id
                                        self.state_channel_id = channel.id
                                        logger.info(f"📂 Found timer state message in #{channel.name}, will migrate to DM")

                                        # Delete the visible message after we've loaded it
                                        try:
                                            await message.delete()
                                            logger.info(f"🗑️ Deleted visible timer state message from #{channel.name}")
                                        except:
                                            pass

                                        return state
                                except json.JSONDecodeError:
                                    continue
                    except discord.Forbidden:
                        continue
                    except Exception as e:
                        logger.debug(f"Error searching channel {channel.name}: {e}")
                        continue

            logger.info(f"📂 Searched {channels_checked} channels, {messages_checked} messages - no timer state found")

            return None

        except Exception as e:
            logger.error(f"❌ Failed to load timer state from Discord: {e}")
            logger.exception("Full error details:")
            return None

    async def load_saved_state(self):
        """Load and restore any saved timer state from Discord, environment variable, or file"""
        logger.info("🔄 Attempting to load saved timer state...")
        state = None

        # Try loading from Discord first (most reliable for ephemeral file systems)
        logger.info("📂 Checking Discord for timer state...")
        state = await self._load_state_from_discord()
        if state:
            logger.info("✅ Loaded timer state from Discord")
        else:
            logger.info("📂 No timer state found in Discord")

        # Fallback to environment variable (for Render/Railway if manually set)
        if not state and 'TIMER_STATE' in os.environ:
            logger.info("📂 Checking environment variable for timer state...")
            try:
                state_json = os.environ['TIMER_STATE']
                state = json.loads(state_json)
                logger.info("✅ Loaded timer state from environment variable")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load timer state from environment variable: {e}")

        # Fallback to file system (for local development)
        if not state and TIMER_STATE_FILE.exists():
            logger.info(f"📂 Checking file system for timer state ({TIMER_STATE_FILE})...")
            try:
                with open(TIMER_STATE_FILE, 'r') as f:
                    state = json.load(f)
                logger.info("✅ Loaded timer state from file")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load timer state from file: {e}")

        if not state:
            logger.info("📂 No saved timer state found anywhere")

        # Load season/week state
        await self._load_season_week_state()

        if not state:
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

            # Save state to DM (migrate from public channel if needed)
            await timer.save_state()

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

    def get_season_week(self) -> Dict:
        """Get current season and week"""
        return {
            'season': self.season,
            'week': self.week
        }

    async def set_season_week(self, season: int, week: int) -> bool:
        """Set the current season and week"""
        if season < 1 or week < 0:
            return False
        self.season = season
        self.week = week
        # Save season/week to state
        await self._save_season_week_state()
        logger.info(f"📅 Season/Week set to Season {season}, Week {week}")
        return True

    async def increment_week(self) -> bool:
        """Increment the week (called when advance happens)"""
        if self.week is None:
            logger.warning("⚠️ Cannot increment week - week not set")
            return False
        self.week += 1
        # Save season/week to state
        await self._save_season_week_state()
        logger.info(f"📅 Week incremented to Week {self.week}")
        return True

    async def _save_season_week_state(self):
        """Save season/week state to Discord"""
        state = {
            'season': self.season,
            'week': self.week,
            'type': 'season_week'  # Mark as season/week state, not timer state
        }
        try:
            # Try to save to DM channel
            bot_owner_id = None
            try:
                app_info = await self.bot.application_info()
                bot_owner_id = app_info.owner.id if app_info.owner else None
            except:
                pass

            if bot_owner_id:
                try:
                    bot_owner = await self.bot.fetch_user(bot_owner_id)
                    dm_channel = bot_owner.dm_channel
                    if not dm_channel:
                        dm_channel = await bot_owner.create_dm()

                    state_json = json.dumps(state)

                    # Try to find existing season/week message
                    async for message in dm_channel.history(limit=10):
                        if (message.author == self.bot.user and
                            message.content.startswith("```json") and
                            '"type": "season_week"' in message.content):
                            await message.edit(content=f"```json\n{state_json}\n```")
                            logger.info("💾 Updated season/week state in DM")
                            return

                    # Create new message
                    await dm_channel.send(content=f"```json\n{state_json}\n```")
                    logger.info("💾 Created season/week state in DM")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Could not save season/week to DM: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save season/week state: {e}")

    async def _load_season_week_state(self):
        """Load season/week state from Discord"""
        try:
            # Try to load from DM channel
            bot_owner_id = None
            try:
                app_info = await self.bot.application_info()
                bot_owner_id = app_info.owner.id if app_info.owner else None
            except:
                pass

            if bot_owner_id:
                try:
                    bot_owner = await self.bot.fetch_user(bot_owner_id)
                    dm_channel = bot_owner.dm_channel
                    if not dm_channel:
                        dm_channel = await bot_owner.create_dm()

                    async for message in dm_channel.history(limit=10):
                        if (message.author == self.bot.user and
                            message.content.startswith("```json") and
                            '"type": "season_week"' in message.content):
                            content = message.content.strip()
                            if content.startswith("```json"):
                                content = content[7:]
                            if content.endswith("```"):
                                content = content[:-3]
                            content = content.strip()

                            try:
                                state = json.loads(content)
                                if state.get('type') == 'season_week':
                                    self.season = state.get('season')
                                    self.week = state.get('week')
                                    logger.info(f"✅ Loaded season/week: Season {self.season}, Week {self.week}")
                                    return
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    logger.debug(f"Could not load season/week from DM: {e}")
        except Exception as e:
            logger.debug(f"Failed to load season/week state: {e}")
