#!/usr/bin/env python3
"""
Channel Manager for CFB 26 League Bot
Manages which channels Harry can make unprompted responses in
"""

import logging
from typing import Set

logger = logging.getLogger('CFB26Bot.ChannelManager')

class ChannelManager:
    """Manages blocked/allowed channels for unprompted responses"""

    def __init__(self):
        # Channels where unprompted responses are BLOCKED
        # Harry can still be @mentioned, but won't jump into conversations
        self.blocked_channels: Set[int] = set()

        # Default blocked channels (can be configured)
        self.blocked_channels.update([
            # Add default blocked channels here if needed
        ])

        logger.info(f"✅ Channel manager initialized ({len(self.blocked_channels)} blocked channels)")

    def is_channel_blocked(self, channel_id: int) -> bool:
        """Check if unprompted responses are blocked in a channel"""
        return channel_id in self.blocked_channels

    def block_channel(self, channel_id: int) -> bool:
        """
        Block unprompted responses in a channel

        Returns:
            True if channel was newly blocked, False if already blocked
        """
        if channel_id in self.blocked_channels:
            return False

        self.blocked_channels.add(channel_id)
        logger.info(f"🔇 Blocked channel: {channel_id}")
        return True

    def unblock_channel(self, channel_id: int) -> bool:
        """
        Unblock unprompted responses in a channel

        Returns:
            True if channel was unblocked, False if wasn't blocked
        """
        if channel_id not in self.blocked_channels:
            return False

        self.blocked_channels.remove(channel_id)
        logger.info(f"🔊 Unblocked channel: {channel_id}")
        return True

    def get_blocked_channels(self) -> list:
        """Get list of blocked channel IDs"""
        return list(self.blocked_channels)

    def get_blocked_count(self) -> int:
        """Get number of blocked channels"""
        return len(self.blocked_channels)

    def can_respond_unprompted(self, channel_id: int) -> bool:
        """
        Check if Harry can make unprompted responses in a channel

        Args:
            channel_id: The Discord channel ID

        Returns:
            True if unprompted responses are allowed, False if blocked
        """
        return not self.is_channel_blocked(channel_id)
