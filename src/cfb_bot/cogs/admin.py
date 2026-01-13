#!/usr/bin/env python3
"""
Admin Cog for CFB 26 League Bot

Provides administrative commands for managing the bot.
Commands:
- /admin set_channel - Set admin notification channel
- /admin add - Add bot admin
- /admin remove - Remove bot admin
- /admin list - List bot admins
- /admin block - Block channel
- /admin unblock - Unblock channel
- /admin blocked - List blocked channels
- /admin config - Configure modules
- /admin sync - Force sync slash commands
- /admin channels - Manage channel whitelist
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..config import Colors, Footers
from ..utils.server_config import server_config, FeatureModule

logger = logging.getLogger('CFB26Bot.Admin')


class AdminCog(commands.Cog):
    """Administrative commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dependencies - set after loading
        self.admin_manager = None
        self.channel_manager = None
        self.timekeeper_manager = None
        logger.info("🔧 AdminCog initialized")

    def set_dependencies(self, admin_manager=None, channel_manager=None, timekeeper_manager=None):
        """Set dependencies after bot is ready"""
        self.admin_manager = admin_manager
        self.channel_manager = channel_manager
        self.timekeeper_manager = timekeeper_manager

    # Command group
    admin_group = app_commands.Group(
        name="admin",
        description="🔧 Admin commands for managing Harry"
    )

    @admin_group.command(name="set_channel", description="Set the channel for admin outputs")
    @app_commands.describe(
        channel="Select a channel",
        channel_id="Or paste a channel ID"
    )
    async def set_channel(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        channel_id: Optional[str] = None
    ):
        """Set the admin notification channel"""
        if not self.admin_manager or not self.admin_manager.is_admin(interaction.user, interaction):
            await interaction.response.send_message("❌ Only admins can set the admin channel!", ephemeral=True)
            return

        if not interaction.guild:
            await interaction.response.send_message("❌ This only works in servers!", ephemeral=True)
            return

        if channel:
            target_channel_id = channel.id
            channel_name = f"#{channel.name}"
        elif channel_id:
            try:
                target_channel_id = int(channel_id.strip())
                fetched = interaction.guild.get_channel(target_channel_id)
                channel_name = f"#{fetched.name}" if fetched else f"<#{target_channel_id}>"
            except ValueError:
                await interaction.response.send_message("❌ Invalid channel ID!", ephemeral=True)
                return
        else:
            await interaction.response.send_message("❌ Provide a channel or channel_id!", ephemeral=True)
            return

        guild_id = interaction.guild.id
        server_config.set_admin_channel(guild_id, target_channel_id)
        await server_config.save_to_discord()

        embed = discord.Embed(
            title="🔧 Admin Channel Set!",
            description=f"Admin outputs will go to: **{channel_name}**",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=Footers.CONFIG)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="add", description="Add a user as bot admin")
    @app_commands.describe(user="The user to make a bot admin")
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        """Add a bot admin"""
        if not self.admin_manager:
            await interaction.response.send_message("❌ Admin manager not available", ephemeral=True)
            return

        if not self.admin_manager.is_admin(interaction.user, interaction):
            await interaction.response.send_message("❌ You need to be a bot admin!", ephemeral=True)
            return

        success = self.admin_manager.add_admin(user.id)

        if success:
            embed = discord.Embed(
                title="✅ Bot Admin Added!",
                description=f"**{user.display_name}** is now a bot admin!",
                color=Colors.SUCCESS
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Already an Admin",
                description=f"{user.display_name} is already a bot admin!",
                color=Colors.WARNING
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="remove", description="Remove a user as bot admin")
    @app_commands.describe(user="The user to remove as bot admin")
    async def remove(self, interaction: discord.Interaction, user: discord.Member):
        """Remove a bot admin"""
        if not self.admin_manager:
            await interaction.response.send_message("❌ Admin manager not available", ephemeral=True)
            return

        if not self.admin_manager.is_admin(interaction.user, interaction):
            await interaction.response.send_message("❌ You need to be a bot admin!", ephemeral=True)
            return

        success = self.admin_manager.remove_admin(user.id)

        if success:
            embed = discord.Embed(
                title="✅ Bot Admin Removed",
                description=f"**{user.display_name}** is no longer a bot admin.",
                color=Colors.ERROR
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Not an Admin",
                description=f"{user.display_name} isn't a bot admin!",
                color=0x808080
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="list", description="List all bot admins")
    async def list_admins(self, interaction: discord.Interaction):
        """List all bot admins"""
        if not self.admin_manager:
            await interaction.response.send_message("❌ Admin manager not available", ephemeral=True)
            return

        admin_ids = self.admin_manager.get_admin_list()

        if not admin_ids:
            embed = discord.Embed(
                title="🔐 Bot Admins",
                description="No bot-specific admins configured.\nDiscord Administrators can use admin commands.",
                color=0x808080
            )
        else:
            admin_info = []
            for aid in admin_ids:
                try:
                    user = await self.bot.fetch_user(aid)
                    admin_info.append(f"• **{user.display_name}** (`{user.name}`)")
                except Exception:
                    admin_info.append(f"• User ID: {aid}")

            embed = discord.Embed(
                title="🔐 Bot Admins",
                description=f"Found **{len(admin_ids)}** bot admin(s):\n\n" + "\n".join(admin_info),
                color=Colors.SUCCESS
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="block", description="Block unprompted responses in a channel")
    @app_commands.describe(channel="The channel to block")
    async def block(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Block unprompted responses"""
        if not self.admin_manager or not self.admin_manager.is_admin(interaction.user, interaction):
            await interaction.response.send_message("❌ Only admins can block channels!", ephemeral=True)
            return

        if not self.channel_manager:
            await interaction.response.send_message("❌ Channel manager not available", ephemeral=True)
            return

        was_blocked = self.channel_manager.block_channel(channel.id)

        if was_blocked:
            embed = discord.Embed(
                title="🔇 Channel Blocked!",
                description=f"I won't make unprompted responses in {channel.mention}.\n\n**@mentions still work!**",
                color=Colors.WARNING
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Already Blocked",
                description=f"{channel.mention} is already blocked!",
                color=0x808080
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="unblock", description="Allow unprompted responses in a channel")
    @app_commands.describe(channel="The channel to unblock")
    async def unblock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Allow unprompted responses"""
        if not self.admin_manager or not self.admin_manager.is_admin(interaction.user, interaction):
            await interaction.response.send_message("❌ Only admins can unblock channels!", ephemeral=True)
            return

        if not self.channel_manager:
            await interaction.response.send_message("❌ Channel manager not available", ephemeral=True)
            return

        was_unblocked = self.channel_manager.unblock_channel(channel.id)

        if was_unblocked:
            embed = discord.Embed(
                title="🔊 Channel Unblocked!",
                description=f"I can respond in {channel.mention} again!",
                color=Colors.SUCCESS
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Not Blocked",
                description=f"{channel.mention} wasn't blocked!",
                color=0x808080
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="blocked", description="Show all blocked channels")
    async def blocked(self, interaction: discord.Interaction):
        """Show all blocked channels"""
        if not self.channel_manager:
            await interaction.response.send_message("❌ Channel manager not available", ephemeral=True)
            return

        blocked_ids = self.channel_manager.get_blocked_channels()

        if not blocked_ids:
            embed = discord.Embed(
                title="🔊 No Blocked Channels",
                description="No channels are blocked!",
                color=Colors.SUCCESS
            )
        else:
            channel_info = []
            for cid in blocked_ids:
                ch = self.bot.get_channel(cid)
                if ch:
                    channel_info.append(f"• {ch.mention}")
                else:
                    channel_info.append(f"• Channel ID: {cid}")

            embed = discord.Embed(
                title="🔇 Blocked Channels",
                description=f"**{len(blocked_ids)}** blocked channel(s):\n\n" + "\n".join(channel_info),
                color=Colors.WARNING
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="config", description="Configure Harry's features for this server")
    @app_commands.describe(
        action="What to do: view, enable, disable, or bulk actions",
        module="Which module to toggle (not needed for enable_all/disable_all)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="view", value="view"),
        app_commands.Choice(name="enable", value="enable"),
        app_commands.Choice(name="disable", value="disable"),
        app_commands.Choice(name="enable_all - Turn on all modules", value="enable_all"),
        app_commands.Choice(name="disable_all - Turn off all modules", value="disable_all"),
    ])
    @app_commands.choices(module=[
        app_commands.Choice(name="ai_chat - /harry, /ask, @mentions", value="ai_chat"),
        app_commands.Choice(name="cfb_data - Player lookup, rankings", value="cfb_data"),
        app_commands.Choice(name="league - Timer, charter, rules", value="league"),
        app_commands.Choice(name="hs_stats - High school stats", value="hs_stats"),
        app_commands.Choice(name="recruiting - On3/247 rankings", value="recruiting"),
        app_commands.Choice(name="fun_games - Rivalry responses (Fuck Oregon!)", value="fun_games"),
    ])
    async def config(
        self,
        interaction: discord.Interaction,
        action: str = "view",
        module: Optional[str] = None
    ):
        """Configure which features are enabled"""
        # Defer IMMEDIATELY to prevent timeout (building the embed is slow)
        if action == "view":
            await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            if action == "view":
                await interaction.followup.send("❌ This only works in servers!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ This only works in servers!", ephemeral=True)
            return

        guild_id = interaction.guild.id

        if action in ["enable", "disable", "enable_all", "disable_all"]:
            is_admin = (
                interaction.user.guild_permissions.administrator or
                (self.admin_manager and self.admin_manager.is_admin(interaction.user, interaction))
            )
            if not is_admin:
                await interaction.response.send_message("❌ Only admins can change settings!", ephemeral=True)
                return

        if action == "view":
            enabled = server_config.get_enabled_modules(guild_id)

            embed = discord.Embed(
                title="⚙️ Harry's Configuration",
                description=f"Settings for **{interaction.guild.name}**",
                color=Colors.PRIMARY
            )

            # Module statuses
            for mod in FeatureModule:
                is_enabled = mod.value in enabled
                status = "✅ Enabled" if is_enabled else "❌ Disabled"
                if mod == FeatureModule.CORE:
                    status = "✅ Always On"

                desc = server_config.get_module_description(mod)
                embed.add_field(name=f"{desc}", value=f"**Status:** {status}", inline=False)

            # Server settings section
            embed.add_field(name="━━━━━━━━━━━━━━━", value="", inline=False)  # Divider

            # Recruiting source
            rec_source = server_config.get_recruiting_source(guild_id)
            rec_name = "On3/Rivals" if rec_source == "on3" else "247Sports"
            embed.add_field(
                name="⭐ Recruiting Data Source",
                value=f"**Source:** {rec_name}",
                inline=True
            )

            # Season/Week info (if timekeeper available)
            if self.timekeeper_manager:
                season_info = self.timekeeper_manager.get_season_week()
                if season_info and season_info.get('season'):
                    week_name = season_info.get('week_name', f"Week {season_info.get('week', '?')}")
                    embed.add_field(
                        name="🏈 Current Season",
                        value=f"**S{season_info['season']}{week_name}**",
                        inline=True
                    )

            # Bot admins count
            if self.admin_manager:
                admin_count = self.admin_manager.get_admin_count()
                embed.add_field(
                    name="🔧 Bot Admins",
                    value=f"**{admin_count}** configured\nUse `/admin list` to view",
                    inline=True
                )

            # Blocked channels (global, not per-guild)
            if self.channel_manager:
                blocked_count = self.channel_manager.get_blocked_count()
                if blocked_count > 0:
                    embed.add_field(
                        name="🚫 Blocked Channels",
                        value=f"**{blocked_count}** blocked (global)\nUse `/admin blocked` to view",
                        inline=True
                    )

            embed.add_field(
                name="ℹ️ More Commands",
                value="`/admin list` - View admins\n"
                      "`/admin blocked` - View blocked channels\n"
                      "`/recruiting source` - Change recruiting source\n"
                      "`/league week` - View current season/week",
                inline=False
            )

            embed.set_footer(text=Footers.CONFIG)
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif action == "enable":
            if not module:
                await interaction.response.send_message("❌ Specify a module to enable!", ephemeral=True)
                return

            try:
                mod = FeatureModule(module)
            except ValueError:
                await interaction.response.send_message(f"❌ Unknown module: {module}", ephemeral=True)
                return

            if mod == FeatureModule.CORE:
                await interaction.response.send_message("Core features are always enabled!", ephemeral=True)
                return

            server_config.enable_module(guild_id, mod)
            await server_config.save_to_discord()

            embed = discord.Embed(
                title="✅ Module Enabled!",
                description=f"**{mod.value.upper()}** is now enabled!",
                color=Colors.SUCCESS
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "disable":
            if not module:
                await interaction.response.send_message("❌ Specify a module to disable!", ephemeral=True)
                return

            try:
                mod = FeatureModule(module)
            except ValueError:
                await interaction.response.send_message(f"❌ Unknown module: {module}", ephemeral=True)
                return

            if mod == FeatureModule.CORE:
                await interaction.response.send_message("Can't disable core features!", ephemeral=True)
                return

            server_config.disable_module(guild_id, mod)
            await server_config.save_to_discord()

            embed = discord.Embed(
                title="❌ Module Disabled",
                description=f"**{mod.value.upper()}** is now disabled.",
                color=Colors.WARNING
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "enable_all":
            # Enable all modules except CORE (which is always on)
            enabled_count = 0
            for mod in FeatureModule:
                if mod != FeatureModule.CORE:
                    server_config.enable_module(guild_id, mod)
                    enabled_count += 1

            await server_config.save_to_discord()

            embed = discord.Embed(
                title="✅ All Modules Enabled!",
                description=f"Enabled **{enabled_count}** modules:\n"
                           f"• AI Chat\n"
                           f"• CFB Data\n"
                           f"• League\n"
                           f"• HS Stats\n"
                           f"• Recruiting\n"
                           f"• Fun & Games",
                color=Colors.SUCCESS
            )
            embed.set_footer(text="Use /admin config view to see full status")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif action == "disable_all":
            # Disable all modules except CORE (which can't be disabled)
            disabled_count = 0
            for mod in FeatureModule:
                if mod != FeatureModule.CORE:
                    server_config.disable_module(guild_id, mod)
                    disabled_count += 1

            await server_config.save_to_discord()

            embed = discord.Embed(
                title="❌ All Modules Disabled",
                description=f"Disabled **{disabled_count}** modules.\n\n"
                           f"✅ **CORE** remains active (/help, /whats_new, etc.)\n\n"
                           f"Use `/admin config enable_all` to restore.",
                color=Colors.WARNING
            )
            embed.set_footer(text="Use /admin config view to see full status")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="sync", description="Force sync slash commands")
    async def sync_commands(self, interaction: discord.Interaction):
        """Force sync slash commands"""
        is_admin = (
            interaction.user.guild_permissions.administrator or
            (self.admin_manager and self.admin_manager.is_admin(interaction.user, interaction))
        )
        if not is_admin:
            await interaction.response.send_message("❌ Only admins can sync commands!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            if interaction.guild:
                synced = await self.bot.tree.sync(guild=interaction.guild)
                embed = discord.Embed(
                    title="✅ Commands Synced!",
                    description=f"Synced **{len(synced)}** command(s) to this server.",
                    color=Colors.SUCCESS
                )
            else:
                synced = await self.bot.tree.sync()
                embed = discord.Embed(
                    title="✅ Global Sync Complete!",
                    description=f"Synced **{len(synced)}** command(s) globally.",
                    color=Colors.SUCCESS
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: {str(e)}", ephemeral=True)

    @admin_group.command(name="channels", description="View/manage which channels Harry can respond in")
    @app_commands.describe(
        action="What to do (leave empty to view)",
        channel="Which channel to configure"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="view - Show current channel status", value="view"),
        app_commands.Choice(name="enable - Enable Harry in this channel", value="enable"),
        app_commands.Choice(name="disable - Disable Harry in this channel", value="disable"),
        app_commands.Choice(name="toggle_rivalry - Toggle rivalry auto-responses", value="toggle_rivalry"),
    ])
    async def channels(
        self,
        interaction: discord.Interaction,
        action: Optional[str] = None,
        channel: Optional[discord.TextChannel] = None
    ):
        """Manage channel whitelist"""
        if not interaction.guild:
            await interaction.response.send_message("❌ This only works in servers!", ephemeral=True)
            return

        guild_id = interaction.guild.id
        target_channel = channel or interaction.channel

        if action is None or action == "view":
            await interaction.response.defer(ephemeral=True)

            enabled_channels = server_config.get_enabled_channels(guild_id)
            is_enabled = server_config.is_channel_enabled(guild_id, target_channel.id)
            rivalry_on = server_config.auto_responses_enabled(guild_id, target_channel.id)

            embed = discord.Embed(
                title="📺 Channel Status",
                color=Colors.PRIMARY
            )

            embed.add_field(
                name=f"#{target_channel.name}",
                value=f"**Commands:** {'✅ Enabled' if is_enabled else '❌ Disabled'}\n**Rivalry Responses:** {'✅ On' if rivalry_on else '❌ Off'}",
                inline=False
            )

            if enabled_channels:
                ch_list = []
                for cid in enabled_channels[:10]:
                    ch = interaction.guild.get_channel(cid)
                    if ch:
                        ch_list.append(f"• #{ch.name}")
                embed.add_field(
                    name="Enabled Channels",
                    value="\n".join(ch_list) if ch_list else "None",
                    inline=False
                )

            embed.set_footer(text="Use /admin channels enable/disable to manage")
            await interaction.followup.send(embed=embed, ephemeral=True)

        elif action in ["enable", "disable", "toggle_rivalry"]:
            is_admin = (
                interaction.user.guild_permissions.administrator or
                (self.admin_manager and self.admin_manager.is_admin(interaction.user, interaction))
            )
            if not is_admin:
                await interaction.response.send_message("❌ Only admins can change channel settings!", ephemeral=True)
                return

            if action == "enable":
                server_config.enable_channel(guild_id, target_channel.id)
                await server_config.save_to_discord()
                embed = discord.Embed(
                    title="✅ Channel Enabled!",
                    description=f"Harry is now enabled in **#{target_channel.name}**",
                    color=Colors.SUCCESS
                )

            elif action == "disable":
                server_config.disable_channel(guild_id, target_channel.id)
                await server_config.save_to_discord()
                embed = discord.Embed(
                    title="❌ Channel Disabled",
                    description=f"Harry is now disabled in **#{target_channel.name}**",
                    color=Colors.WARNING
                )

            elif action == "toggle_rivalry":
                # Toggle rivalry auto-responses
                is_on = server_config.toggle_auto_responses(guild_id, target_channel.id)
                await server_config.save_to_discord()
                status = "ON 🦆" if is_on else "OFF"
                embed = discord.Embed(
                    title=f"🏈 Rivalry Responses: {status}",
                    description=f"Auto-responses for #{target_channel.name} are now **{status}**",
                    color=Colors.SUCCESS if is_on else Colors.WARNING
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="zyte", description="Check Zyte API usage and estimated costs")
    async def zyte_usage(self, interaction: discord.Interaction):
        """Check Zyte API usage statistics"""
        if not interaction.guild:
            await interaction.response.send_message("❌ This only works in servers!", ephemeral=True)
            return

        # Check if user is admin
        is_admin = (
            interaction.user.guild_permissions.administrator or
            (self.admin_manager and self.admin_manager.is_admin(interaction.user, interaction))
        )
        if not is_admin:
            await interaction.response.send_message("❌ Only admins can view Zyte usage!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Get On3 scraper usage
        from .recruiting import get_recruiting_scraper
        guild_id = interaction.guild.id
        scraper, source_name = get_recruiting_scraper(guild_id)

        # Check if it's On3 scraper (has Zyte)
        if source_name == "On3/Rivals" and hasattr(scraper, 'get_zyte_usage'):
            usage = scraper.get_zyte_usage()

            embed = discord.Embed(
                title="💰 Zyte API Usage Report",
                description=f"Premium Cloudflare bypass statistics for **{interaction.guild.name}**",
                color=Colors.PRIMARY
            )

            # Availability
            status = "✅ Available" if usage['is_available'] else "❌ Not configured"
            embed.add_field(
                name="📡 Status",
                value=status,
                inline=False
            )

            if usage['is_available']:
                # Usage stats
                embed.add_field(
                    name="📊 Requests This Session",
                    value=f"**{usage['request_count']}** requests",
                    inline=True
                )

                # Cost
                embed.add_field(
                    name="💵 Estimated Cost",
                    value=f"**${usage['estimated_cost']:.4f}**",
                    inline=True
                )

                # Rate
                embed.add_field(
                    name="💳 Rate",
                    value=f"${usage['cost_per_1k']:.3f} per 1K requests",
                    inline=True
                )

                # Projections
                monthly_projection = usage['request_count'] * 30  # rough estimate
                monthly_cost = (monthly_projection * usage['cost_per_1k']) / 1000

                embed.add_field(
                    name="📈 Monthly Projection",
                    value=f"~{monthly_projection:,} requests\n~${monthly_cost:.2f}/month",
                    inline=False
                )

                # Info
                embed.add_field(
                    name="ℹ️ How It Works",
                    value="Zyte only triggers when free methods (Playwright, Cloudscraper) are blocked by Cloudflare. "
                          "This keeps costs minimal while ensuring reliability.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Setup Required",
                    value="Add `ZYTE_API_KEY` to environment variables to enable premium bypass.",
                    inline=False
                )

            embed.set_footer(text="💡 Session resets on bot restart")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="ℹ️ Zyte Not Used",
                description=f"Currently using **{source_name}** which doesn't require Zyte API.",
                color=Colors.WARNING
            )
            embed.add_field(
                name="💡 Tip",
                value="Switch to On3/Rivals with `/recruiting source on3` to enable Zyte bypass.",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @admin_group.command(name="ai", description="Check AI API usage, token consumption, and estimated costs")
    async def ai_usage(self, interaction: discord.Interaction):
        """Check AI token usage and cost statistics"""
        if not interaction.guild:
            await interaction.response.send_message("❌ This only works in servers!", ephemeral=True)
            return

        # Check if user is admin
        is_admin = (
            interaction.user.guild_permissions.administrator or
            (self.admin_manager and self.admin_manager.is_admin(interaction.user, interaction))
        )
        if not is_admin:
            await interaction.response.send_message("❌ Only admins can view AI usage!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Get AI integration from bot
        if not hasattr(self.bot, 'ai_assistant') or not self.bot.ai_assistant:
            embed = discord.Embed(
                title="ℹ️ AI Not Available",
                description="AI integration is not currently configured.",
                color=Colors.WARNING
            )
            embed.add_field(
                name="⚠️ Setup Required",
                value="Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to environment variables to enable AI features.",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Get usage stats
        usage = self.bot.ai_assistant.get_token_usage()

        embed = discord.Embed(
            title="🤖 AI API Usage Report",
            description=f"Token consumption and cost statistics for **{interaction.guild.name}**",
            color=Colors.PRIMARY
        )

        # Overall stats
        embed.add_field(
            name="📊 Total Requests",
            value=f"**{usage['total_requests']:,}** queries",
            inline=True
        )

        embed.add_field(
            name="🎯 Total Tokens",
            value=f"**{usage['total_tokens']:,}** tokens",
            inline=True
        )

        embed.add_field(
            name="💰 Total Cost",
            value=f"**${usage['total_cost']:.4f}**",
            inline=True
        )

        # OpenAI breakdown
        if usage['openai_tokens'] > 0:
            embed.add_field(
                name="🟢 OpenAI (GPT-3.5-turbo)",
                value=f"**{usage['openai_tokens']:,}** tokens\n${usage['openai_cost']:.4f}",
                inline=True
            )

        # Anthropic breakdown
        if usage['anthropic_tokens'] > 0:
            embed.add_field(
                name="🔵 Anthropic (Claude 3 Haiku)",
                value=f"**{usage['anthropic_tokens']:,}** tokens\n${usage['anthropic_cost']:.4f}",
                inline=True
            )

        # Add spacing field if needed
        if usage['openai_tokens'] > 0 or usage['anthropic_tokens'] > 0:
            embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Monthly projection
        if usage['total_requests'] > 0:
            avg_tokens_per_request = usage['total_tokens'] / usage['total_requests']
            avg_cost_per_request = usage['total_cost'] / usage['total_requests']
            
            # Estimate based on 100 requests/month (conservative)
            monthly_requests = 100
            monthly_tokens = int(monthly_requests * avg_tokens_per_request)
            monthly_cost = monthly_requests * avg_cost_per_request

            embed.add_field(
                name="📈 Monthly Projection (est. 100 queries)",
                value=f"~{monthly_tokens:,} tokens\n~${monthly_cost:.2f}/month",
                inline=False
            )

        # Info
        embed.add_field(
            name="ℹ️ How It Works",
            value="AI is used for `/harry`, `/ask`, `/summarize` commands and @mentions. "
                  "Costs are typically minimal - OpenAI GPT-3.5 and Anthropic Claude Haiku are very affordable.",
            inline=False
        )

        embed.set_footer(text="💡 Session stats reset on bot restart")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Required setup function for loading cog"""
    cog = AdminCog(bot)
    await bot.add_cog(cog)
    logger.info("✅ AdminCog loaded")
