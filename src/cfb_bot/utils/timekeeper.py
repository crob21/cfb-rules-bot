#!/usr/bin/env python3
"""
Timekeeper Module for CFB 26 League Bot
Manages advance countdown timers with notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import discord

logger = logging.getLogger('CFB26Bot.Timekeeper')

class AdvanceTimer:
    """Manages the 48-hour advance countdown timer"""

    def __init__(self, channel: discord.TextChannel, bot: discord.Client):
        self.channel = channel
        self.bot = bot
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_active = False
        self.task: Optional[asyncio.Task] = None
        self.notifications_sent = {
            24: False,
            12: False,
            6: False,
            1: False
        }

    def start_countdown(self) -> bool:
        """Start the 48-hour countdown"""
        if self.is_active:
            logger.warning("⚠️ Countdown already active")
            return False

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=48)
        self.is_active = True
        self.notifications_sent = {24: False, 12: False, 6: False, 1: False}

        # Start the monitoring task
        self.task = asyncio.create_task(self._monitor_countdown())

        logger.info(f"⏰ Countdown started at {self.start_time}")
        logger.info(f"⏰ Countdown will end at {self.end_time}")
        return True

    def stop_countdown(self) -> bool:
        """Stop the countdown"""
        if not self.is_active:
            return False

        self.is_active = False
        if self.task and not self.task.done():
            self.task.cancel()

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

                elif total_hours <= 12 and not self.notifications_sent[12]:
                    await self._send_notification(12)
                    self.notifications_sent[12] = True

                elif total_hours <= 6 and not self.notifications_sent[6]:
                    await self._send_notification(6)
                    self.notifications_sent[6] = True

                elif total_hours <= 1 and not self.notifications_sent[1]:
                    await self._send_notification(1)
                    self.notifications_sent[1] = True

                # Check if time is up
                if total_hours <= 0:
                    await self._send_times_up()
                    self.is_active = False
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

    def get_timer(self, channel: discord.TextChannel) -> AdvanceTimer:
        """Get or create a timer for a channel"""
        if channel.id not in self.timers:
            self.timers[channel.id] = AdvanceTimer(channel, self.bot)
        return self.timers[channel.id]

    def start_timer(self, channel: discord.TextChannel) -> bool:
        """Start a timer for a channel"""
        timer = self.get_timer(channel)
        return timer.start_countdown()

    def stop_timer(self, channel: discord.TextChannel) -> bool:
        """Stop a timer for a channel"""
        if channel.id not in self.timers:
            return False
        return self.timers[channel.id].stop_countdown()

    def get_status(self, channel: discord.TextChannel) -> Dict:
        """Get timer status for a channel"""
        if channel.id not in self.timers:
            return {
                'active': False,
                'message': 'No countdown active'
            }
        return self.timers[channel.id].get_status()
