from __future__ import annotations

import discord
from discord import Color
from discord import ui
from discord.ui import Button,button, View
from discord.ext import commands
from discord.ext.commands import *
from datetime import timedelta
from typing import Optional, Literal
import asyncio
from typing import Optional
import sys
import humanfriendly
import datetime
import psutil
from discord.ui import Button, View, button
import sqlite3
import os

from tools.bytesio import dom_color

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis
from tools.View import Invite

class Info(commands.Cog):
	def __init__(self, Steal):
		self.bot = Steal

	@command(
			name="invite",
			aliases=["inv", "link"],
			description="Sends the support server invite link.",
			usage="invite"
	)
	async def invite(self, ctx: StealContext):

		view = Invite()

		out = await ctx.reply(embed=discord.Embed(
			description=f"Join the support server or add the [**owner**](<https://discord.com/users/{self.bot.owner_ids[0]}>)",
			color=Colors.BASE_COLOR
		).set_author(
			name=ctx.author,
			icon_url=ctx.author.display_avatar.url or None
		)
		, view=view)
		view.message = out

	@command(
			name="credits",
			description="Sends the credits of the bot.",
			usage="credits"
	)
	async def credits(self, ctx: StealContext):

		view = Invite()

		embed = discord.Embed(
			color = Colors.BASE_COLOR
		).add_field(
			name="Oxy:",
			value=f"> [**Bot owner and main developer**](<https://discord.com/users/{self.bot.owner_ids[0]}>).",
			inline=False
		).add_field(
			name=f"Ziggy:",
			value=f"> [**Is ziggy.**](<https://discord.com/users/{self.bot.owner_ids[1]}>)",
			inline=False
		).set_author(
			name=ctx.author,
			icon_url=ctx.author.display_avatar.url or None
		)

		out = await ctx.send(embed=embed, view=view)

		view.message = out

	@command(
			name="userinfo",
			description="Gives userinfo.",
			aliases=["ui", "uinfo"],
			usage='userinfo [user]'
	)
	@cooldown(1,15, commands.BucketType.user)
	@guild_only()
	async def userinfo(self, ctx:StealContext, member: Optional[discord.Member] = Author) -> None:

		timestamp1 = discord.utils.format_dt(member.created_at, style="F")
		
		timestamp2 = [discord.utils.format_dt(member.joined_at, style="F") if member.joined_at else "?"] if not isinstance(ctx.channel, discord.DMChannel) else "?"

		if ctx.guild:
			roles = member.roles[-1:0:-1]

			if roles:

				rolelist = f", ".join([r.mention for r in member.roles if r != ctx.guild.default_role])
				if len(rolelist) > 200:
					continuation_string = ("(+{numeric_number})")

					available_length = 150 - len(continuation_string)

					role_chunks = []
					remaining_roles = 0
					for r in roles:
						chunk = f"{r.mention},"
						chunk_size = len(chunk)
						if chunk_size < available_length:
							available_length -= chunk_size
							role_chunks.append(chunk)
						else:
							remaining_roles += 1
					role_chunks = role_chunks[::-1]
					role_chunks = role_chunks[::-1]
					role_chunks.append(continuation_string.format(numeric_number=remaining_roles))
					rolelist = "".join(role_chunks)
			else:
				rolelist = None
		else:
			rolelist = "?"

		def guns(user:discord.Member):
			if isinstance(user, discord.Member):
				has_emote_status = any([a.emoji.is_custom_emoji() for a in user.activities if getattr(a, 'emoji', None)])
 
				return any([user.display_avatar.is_animated(), has_emote_status, user.premium_since, user.guild_avatar, user.banner])

		info = discord.Embed(
			title=f"{member} {Emojis.NITRO if guns(member) else ''} {Emojis.BOOST if member in ctx.guild.premium_subscribers else ''}",
			color=Colors.BASE_COLOR,
		).add_field(
			name=f'Created at:',
			value=f'{timestamp1}',
			inline=True
		).add_field(
			name='Joined at:',
			value=f'{timestamp2[0]}',
			inline=True
		).add_field(
			name='Roles:',
			value=f'{rolelist}',
			inline=False
		)
		

		await ctx.send(
			embed=info.set_author(
				name=f"{member.name}",
				icon_url=member.display_avatar.url if member.display_avatar else None
			)
			)

	@command(
			name="serverinfo",
			description="Gives server info.",
			usage="serverinfo",
			aliases=["si"]
	)
	@cooldown(1,15, BucketType.user)
	@guild_only()
	async def serverinfo(self, ctx: StealContext) -> None:

		server_owner = ctx.guild.owner
		server_verification = ctx.guild.verification_level
		server_boosts = ctx.guild.premium_subscription_count
		server_boost_level = ctx.guild.premium_tier
		server_members = round(len([i for i in ctx.guild.members]))
		server_members_formatted = (f"{server_members:,}")
		server_text_channels = len([channel for channel in ctx.guild.channels if isinstance(channel, discord.TextChannel)])
		server_voice_channels = len([channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)])
		server_roles = ctx.guild.roles[-1:0:-1]
		server_creation = discord.utils.format_dt(ctx.guild.created_at)
		server_creation_relative = discord.utils.format_dt(ctx.guild.created_at, style="R")
		if server_roles:
			role_list = f", ".join([r.mention for r in ctx.guild.roles if r != ctx.guild.default_role])
			if len(role_list) > 200:
				continuation_string = ("(+{numeric_number})")

				available_length = 150 - len(continuation_string)

				role_chunks = []
				remaining_roles = 0
				for r in server_roles:
					chunk = f"{r.mention},"
					chunk_size = len(chunk)
					if chunk_size < available_length:
						available_length -= chunk_size
						role_chunks.append(chunk)
					else:
						remaining_roles += 1
				role_chunks = role_chunks[::-1]
				role_chunks = role_chunks[::-1]
				role_chunks.append(continuation_string.format(numeric_number=remaining_roles))
				role_list = "".join(role_chunks)
		else:
			role_list = None
		
		avatarbytes = await ctx.guild.icon.read() if ctx.guild.icon else None
		if avatarbytes is not None:
			dominant_color = dom_color(avatarbytes)
			from isHex import isHex
			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

		embed = discord.Embed(
			description=f'{server_creation} ({server_creation_relative})',
			color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]) if avatarbytes else Colors.BASE_COLOR
		).add_field(
			name='Information',
			value=f'>>> Owner: {server_owner}\nVerification level: {str(server_verification)}\nNitro boosts: {str(server_boosts)} (`Level {str(server_boost_level)}`)',
			inline=True
		).add_field(
			name='Statistics',
			value=f'>>> Members: {server_members_formatted}\nText channels: {str(server_text_channels)}\nVoice channels: {str(server_voice_channels)}',
			inline=True
		).add_field(
			name='Roles',
			value=f'>>> {role_list}',
			inline=False
		).set_author(
			name=ctx.guild.name,
			url=f"https://discord.com/channels/{ctx.guild.id}/",
			icon_url=ctx.guild.icon.url if ctx.guild.icon else None
		)
		await ctx.send(embed=embed)

	@command(
			name="channelinfo",
			description="Gives channel info.",
			usage="channelinfo",
			aliases=["ci"]
	)
	async def channelinfo(self, ctx: StealContext, channel: Optional[discord.abc.GuildChannel] = None):

		if not channel: channel = ctx.channel

		embed = (
			discord.Embed(color=Colors.BASE_COLOR, title=channel.name)
			.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar)
			.add_field(name="Channel ID", value=f"`{channel.id}`", inline=True)
			.add_field(name="Type", value=str(channel.type), inline=True)
			.add_field(
				name="Guild",
				value=f"{channel.guild.name} (`{channel.guild.id}`)",
				inline=True,
			)
			.add_field(
				name="Category",
				value=f"{channel.category.name} (`{channel.category.id}`)",
				inline=False,
			)
			.add_field(name="Topic", value=f"`{channel.topic}`" or "N/A", inline=True)
			.add_field(
				name="Created At",
				value=f"{discord.utils.format_dt(channel.created_at, style='F')} ({discord.utils.format_dt(channel.created_at, style='R')})",
				inline=False,
			)
		)

		await ctx.send(embed=embed)

	@command(
		name = "botinfo",
		usage = "botinfo",
		aliases = ["bi", "bot"],
		description = "Get information about the bot."
	)
	@cooldown(1, 5, commands.BucketType.user)
	async def botinfo(self, ctx: Context) -> None:
		commands = [command for command in set(self.bot.walk_commands()) if command.cog_name not in ['BotManagement', 'Auth', 'Profile', 'Bs']]

		embed = discord.Embed(
			title = f"{self.bot.user.name.split('#')[0]}",
			color = Colors.BASE_COLOR,
			description=f"I am {self.bot.user}, I have `{len(commands)}` commands. I'm in `{len(self.bot.guilds):,}` guilds serving `{len(self.bot.users):,}` users. I'm using `{psutil.cpu_percent()}%` of my CPU, `{psutil.virtual_memory().percent}%` of my RAM, running on `Dpy version {discord.__version__}` and `Python Version {sys.version.split(' (')[0]}`"
		)
		embed.set_thumbnail(url=self.bot.user.display_avatar.url)
		embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)

		await ctx.send(embed=embed)

	@command(
			name="inviteinfo",
			description="Gives invite info.",
			aliases=["ii"],
			usage="inviteinfo"
	)
	@cooldown(1,15, BucketType.user)
	async def inviteinfo(self, ctx: StealContext, invite: discord.Invite) -> None:

		invite_inviter = invite.inviter if invite.inviter else "Vanity URL."
		invite_channel = invite.channel.name
		invite_server_creation = discord.utils.format_dt(invite.guild.created_at)
		invite_server_creation_relative = discord.utils.format_dt(invite.guild.created_at, style="R")
		invite_creation_relative = discord.utils.format_dt(invite.created_at, style="R") if invite.created_at else "?"
		invite_server_verification = invite.guild.verification_level
		invite_server_boosts = invite.guild.premium_subscription_count
		invite_server_name = invite.guild.name

		if invite_server_boosts >= 3:
			level = 1
		if invite_server_boosts >= 7:
			level = 2
		if invite_server_boosts >= 14:
			level = 3
		if invite_server_boosts < 3:
			level = 0

		avatarbytes = await invite.guild.icon.read() if invite.guild.icon else None
		if avatarbytes is not None:
			dominant_color = dom_color(avatarbytes)
			from isHex import isHex
			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

		embed = discord.Embed(
			description=f'{invite_server_creation} ({invite_server_creation_relative})',
			color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]) if avatarbytes else Colors.BASE_COLOR
		).add_field(
			name='Information',
			value=f'>>> Inviter: {invite_inviter}\nChannel: {invite_channel}\nCreated: {invite_creation_relative}',
			inline=True
		).add_field(
			name='Guild',
			value=f'>>> Name: {invite_server_name}\nNitro Boosts: {invite_server_boosts} (`Level {level}`)\nVerification Level: {invite_server_verification}',
			inline=True
		).set_author(
			name=f"{invite.id} ({invite.guild.id})",
			url=invite.url,
			icon_url=invite.guild.icon.url if invite.guild.icon else None
		)
		await ctx.send(embed=embed)

		async def lines(self) -> int:

			lines = 0
			for d in [x[0] for x in os.walk("./") if not ".git" in x[0]]:
				for file in os.listdir(d):
					if file.endswith(".py"):
						lines += len(open(f"{d}/{file}", "r").read().splitlines())

			return lines

async def setup(bot):
	await bot.add_cog(Info(bot))