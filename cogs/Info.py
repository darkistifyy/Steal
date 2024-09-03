from __future__ import annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
from typing import Optional
from tools.Config import Auth
import sys
import humanize.number
import psutil
import os
from discord import Spotify
import requests
import humanfriendly
import humanize
import time
import asqlite
import json

from tools.View import DownloadAsset
from tools.bytesio import dom_color
from tools.View import CustomView
import datetime

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional, Union
from tools.Config import Colors, Emojis, Flags
from tools.View import Invite
import math
import asyncio

class Info(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = "Discord info commands."

	@command(
			name="invite",
			aliases=["support"],
			description="Sends the support server invite link.",
			brief="invite",
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
			brief="credits",
			description="Sends the credits of the bot.",
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
			brief="userinfo @someguy",
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

		flag_to_emoji = {
			discord.UserFlags.verified_bot_developer : Flags.VERIFIED_DEV,
			discord.UserFlags.active_developer : Flags.ACTIVE_DEV,
			discord.UserFlags.bug_hunter : Flags.BUG_HUNTER,
			discord.UserFlags.bug_hunter_level_2 : Flags.BUG_HUNTER2,
			discord.UserFlags.discord_certified_moderator : Flags.MODERATOR,
			discord.UserFlags.hypesquad_balance : Flags.BALANCE,
			discord.UserFlags.hypesquad_brilliance : Flags.BRILLIANCE,
			discord.UserFlags.hypesquad_bravery : Flags.BRAVERY,
			discord.UserFlags.partner : Flags.PARTNER
		}
		
		def guns(user:discord.Member):
			if isinstance(user, discord.Member):
				has_emote_status = any([a.emoji.is_custom_emoji() for a in user.activities if getattr(a, 'emoji', None)])
 
				return any([user.display_avatar.is_animated(), has_emote_status, user.premium_since, user.guild_avatar, user.banner])


		badges = [
			flag_to_emoji.get(flag, "❓")
			for flag in member.public_flags.all()
		]

		if guns(member): badges.append(Flags.NITRO)
		if member in ctx.guild.premium_subscribers: badges.append(Flags.BOOST)


		info = discord.Embed(
			title=f"{member} {' '.join(badges)}",
			description="",
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

		if member.activities:
			for activity in member.activities:
				if isinstance(activity, Spotify):
					info.description = f"🎵 {member} is listening to [{activity.title}]({activity.track_url}) by {activity.artist}."
		

		await ctx.send(
			embed=info.set_author(
				name=f"{ctx.author.name}",
				icon_url=ctx.author.display_avatar.url or None
			).set_thumbnail(
				url=member.display_avatar.url or None
			)
			)

	@command(
			name="serverinfo",
			description="Gives server info.",
			aliases=["si"],
			brief="serverinfo",
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
			dominant_color = await self.bot.dominant_color(avatarbytes)

		embed = discord.Embed(
			description=f'{server_creation} ({server_creation_relative})',
			color=dominant_color if dominant_color else Colors.BASE_COLOR
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
			aliases=["ci"],
			brief="channelinfo #general"
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
		aliases = ["bi"],
		description = "Get information about the bot.",
		brief="botinfo"
	)
	@cooldown(1, 5, commands.BucketType.user)
	async def botinfo(self, ctx: Context) -> None:
		commands = [command for command in set(self.bot.walk_commands())] #if command.cog_name not in ['BotManagement', 'Auth', 'Profile', 'Bs

		embed = discord.Embed(
			title = f"Bot information",
			color = Colors.BASE_COLOR,
			description=f"I am [**{self.bot.user.name.split("#")[0]}**]({Auth.invite})\n>>> **Commands:** `{len(commands):,}`\n**Lines:**`{(self.bot.lines):,}`\n**Guilds:**`{len(self.bot.guilds):,}`\n**Users:**`{len(self.bot.users):,}`\n**Command prefix:** `{await self.bot.get_prefix(ctx.message)}`"
		)
		embed.add_field(
			name="CPU %",
			value=f"`{psutil.cpu_percent()}%`",inline= True
		).add_field(
			name="RAM %",
			value=f"`{psutil.virtual_memory().percent}%`",inline=True
		).add_field(
			name="Uptime",
			value=f"`{humanize.naturaldelta(datetime.timedelta(seconds=int(round(time.time()-self.bot.startTime)))).capitalize()}`",inline=True
		)

		embed.set_thumbnail(url=self.bot.user.display_avatar.url)
		embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)

		await ctx.send(embed=embed)

	@command(
			name="inviteinfo",
			description="Gives invite info.",
			aliases=["ii"],
			brief="inviteinfo discord.gg/fembakery"
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
			dominant_color = await self.bot.dominant_color(avatarbytes)

		embed = discord.Embed(
			description=f'{invite_server_creation} ({invite_server_creation_relative})',
			color=dominant_color if dominant_color else Colors.BASE_COLOR
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

	@command(
			name="emojiinfo",
			aliases=["ei"],
			description="Gives emoji info.",
			brief="emojiinfo :twerk:",
	)
	@guild_only()
	async def emojiinfo(self, ctx: StealContext, *, emoji: Union[discord.Emoji, discord.PartialEmoji]):

		embed = discord.Embed(
			color=Colors.BASE_COLOR, title=emoji.name, timestamp=emoji.created_at
		)

		embed.set_thumbnail(url=emoji.url)

		embed.add_field(name="Animated", value=emoji.animated)
		embed.add_field(name="Link", value=f"[emoji]({emoji.url})")
		embed.set_footer(text=f"id: {emoji.id}")
		view = DownloadAsset(emoji.url)
		view.message = await ctx.reply(embed=embed, view=view)

	@command(
		name="spotify",
		description="Shows a users currently listening info.",
		aliases=["song", "nowplaying"],
		brief="spotify @someguy",
	)
	@cooldown(1,15, BucketType.user)
	@guild_only()
	async def spotify(self, ctx: StealContext, member:Optional[discord.Member] = Author):
		if member.activities:

			for activity in member.activities:

				if isinstance(activity, Spotify):

					response = requests.get(activity.album_cover_url)
					bytes = response.content
					if bytes is not None:
						dominant_color = await self.bot.dominant_color(bytes)

					info = discord.Embed(
						title=f"{activity.title}",
						url=f"{activity.track_url}",
						description=f"🎵 {member} is **listening to** [{activity.title}]({activity.track_url})",
						color=dominant_color if dominant_color else Colors.BASE_COLOR
					).add_field(
						name="Lyricist/Artist",
						value=f"{activity.artist}"
					).add_field(
						name="Album",
						value=f"{activity.album}"
					).set_footer(
						text=f"Started listening at {activity.created_at.strftime('%H:%M')}"
					).set_thumbnail(
						url=activity.album_cover_url
					)
					return await ctx.reply(embed=info)
		
		await ctx.deny(f"{member.mention} is not listening to music right now.")

	@command(
		name="game",
		description="Shows the game the user is currently playing.",
		aliases=["playing"],
		brief="game @someguy",
	)
	@cooldown(1,15, BucketType.user)
	@guild_only()
	async def game(self, ctx: StealContext, member:Optional[discord.Member] = Author):
		if member.activities:

			for activity in member.activities:

				if activity.type == discord.ActivityType.playing:

					response = requests.get(member.display_avatar.url)
					bytes = response.content
					if bytes is not None:
						dominant_color = await self.bot.dominant_color(bytes)

					info = discord.Embed(
						title=f"{activity.name}",
						description=f"🎮 {member} is **playing** {activity.name}",
						color=dominant_color if dominant_color else Colors.BASE_COLOR
					).add_field(
						name="Platform",
						value=f"{activity.platform}"
					).add_field(
						name="Started at",
						value=f"Started playing at {activity.created_at.strftime('%H:%M')}"
					).set_thumbnail(
						url=member.display_avatar.url
					)
					return await ctx.reply(embed=info)
		
		await ctx.deny(f"{member.mention} is not playing any games right now.")


	@command(
		name="activity",
		description="Shows the current users activity.",
		aliases=["doing", "act", "status"],
		brief="activity @someguy",
	)
	@cooldown(1,15, BucketType.user)
	@guild_only()
	async def activity(self, ctx: StealContext, member:Optional[discord.Member] = Author):
		if member.activities:

			for activity in member.activities:

				if isinstance(activity, Spotify):

					response = requests.get(activity.album_cover_url)
					bytes = response.content
					dominant_color = None
					if bytes is not None:
						dominant_color = await self.bot.dominant_color(bytes)

					info = discord.Embed(
						title=f"{activity.title}",
						url=f"{activity.track_url}",
						description=f"🎵 {member} is **{str(activity.type).split('.')[1].capitalize()} to** [{activity.title}]({activity.track_url})",
						color=dominant_color if dominant_color else Colors.BASE_COLOR
					).add_field(
						name="Lyricist/Artist",
						value=f"{activity.artist}"
					).add_field(
						name="Album",
						value=f"{activity.album}"
					).set_footer(
						text=f"Started listening at {activity.created_at.strftime('%H:%M')}"
					).set_thumbnail(
						url=activity.album_cover_url
					)
					return await ctx.reply(embed=info)

				elif activity.type == discord.ActivityType.playing:

					response = requests.get(member.display_avatar.url)
					bytes = response.content
					if bytes is not None:
						dominant_color = await self.bot.dominant_color(bytes)

					info = discord.Embed(
						title=f"{activity.name}",
						description=f"🎮 {member} is **playing** {activity.name}",
						color=dominant_color if dominant_color else Colors.BASE_COLOR
					).add_field(
						name="Platform",
						value=f"{activity.platform}"
					).add_field(
						name="Started at",
						value=f"Started playing at {activity.created_at.strftime('%H:%M')}"
					).set_thumbnail(
						url=member.display_avatar.url
					)
					return await ctx.reply(embed=info)
		
				
				elif activity.type == discord.ActivityType.streaming:

					response = requests.get(activity.large_image_url)
					bytes = response.content
					if bytes is not None:
						dominant_color = await self.bot.dominant_color(bytes)

					info = discord.Embed(
						title=f"{activity.name}",
						url=activity.url,
						description=f"🖥️ {member} is **{str(activity.type).split('.')[1].capitalize()}** {activity.game}",
						color=dominant_color if dominant_color else Colors.BASE_COLOR
					).add_field(
						name="Platform",
						value=f"{activity.platform if activity.platform else 'Not avaliable.'}"
					).add_field(
						name="Twitch Name",
						value=f"{activity.twitch_name}"
					).set_footer(
						text=f"Started playing at {activity.created_at.strftime('%H:%M')}"
					).set_thumbnail(
						url=activity.large_image_url
					)
					return await ctx.reply(embed=info)

		
		await ctx.deny(f"{member.mention} is not doing a supported activity right now.")

	@command(
			name='nitrohavers',
			description='Users with nitro.',
			aliases=['nhavers', 'nhs', 'premiumusers'],
			brief="nitrohavers",
	)
	@guild_only()
	async def nhavers(self, ctx: StealContext) -> None:
		def guns(user:discord.Member):
			if isinstance(user, discord.Member):
				has_emote_status = any([a.emoji.is_custom_emoji() for a in user.activities if getattr(a, 'emoji', None)])
 
				if not user.bot:
					return any([user.display_avatar.is_animated(), has_emote_status, user.premium_since, user.guild_avatar, user.banner])
		
		nhavers_ = [mem for mem in ctx.guild.members if guns(mem)]

		if not nhavers_:
			return await ctx.warn(f"There are no **premium users** in this server.")
			

		count = 0
		embeds = []
		
		entries = [
			f"`{i}` {b.mention} (`{b}`)"
			for i, b in enumerate(nhavers_, start=1)
		]

		l = 5

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Nitro Users (`{len(entries)}`)",
			description=""
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Nitro Users (`{len(entries)}`)",
					description=""
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)

	@command(
			name="invites",
			description='Invites to this guild.',
			aliases=['invs'],
			brief="invites",
	)
	@guild_only()
	async def invites(self, ctx: StealContext) -> None:
		invites = await ctx.guild.invites() or []
	
		if ctx.guild.vanity_url:
			invites.append(ctx.guild.vanity_url_code)

		count = 0
		embeds = []

		if not invites:
			return await ctx.warn("There are no **invites** to this guild.")

		entries = [
			f"`{i}` `{b.code}` ({b.inviter})"
			for i, b in enumerate(invites, start=1)
		]

		l = 10

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Invites (`{len(entries)}`)",
			description=""
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Invites (`{len(entries)}`)",
					description=""
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)
	
	@command(
			name="boosters",
			description='Users server boosting.',
			brief="boosters",
	)
	@guild_only()
	async def boosters(self, ctx: StealContext) -> None:
		boosters = [sub for sub in ctx.guild.premium_subscribers]

		if not boosters:
			return await ctx.warn(f"There are no **boosters** in this server.")
			

		count = 0
		embeds = []
		
		entries = [
			f"`{i}` {b.mention} (`{b}`)"
			for i, b in enumerate(boosters, start=1)
		]

		l = 5

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Boosters (`{len(entries)}`)",
			description=""
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Boosters (`{len(entries)}`)",
					description=""
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)     


	@command(
			name="bans",
			description='Ban entries for this guild.',
			brief="bans",
	)
	@guild_only()
	async def bans(self, ctx: StealContext) -> None:
		bans = [ban async for ban in ctx.guild.bans(limit=None)] or []

		count = 0
		embeds = []

		if not bans:
			return await ctx.deny("There are no users banned from this guild.")

		entries = [
			f"`{i}` **{b.user}** - **{b.reason}**"
			for i, b in enumerate(bans, start=1)
		]

		l = 10

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Bans (`{len(entries)}`)",
			description=""
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Bans (`{len(entries)}`)",
					description=""
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)
	

	@group(
			name='server',
			description='Manages server.',
			aliases=['guild'],
			brief="server",
	)
	async def server(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.plshelp()

	@server.command(
			name="lockdown",
			description="Locks every channel in the server.",
			brief="lockdown @member lol",
	)
	async def lockdown(self, ctx: StealContext, target:Optional[discord.Role], reason: Optional[str] = "No reason."):

		reason += ' | Lockdown executed by {}'.format(ctx.author)
		if target is None: target = ctx.guild.default_role

		if isinstance(target, discord.Role):
			perms = target.permissions
			if target.position > ctx.guild.me.top_role.position:
				return await ctx.warn(f"I cannot manage {target.mention}.")
			if perms.manage_channels:
				return await ctx.warn(f"I cannot manage {target.mention}.")			
			if not ctx.author == ctx.guild.owner:
				if target.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")		
										
		if isinstance(target, discord.Member):
			perms = target.guild_permissions
			if target == ctx.guild.owner:
				return await ctx.warn("You cannot manage the server owner.")
			if target.top_role.position > ctx.guild.me.top_role.position:
				return await ctx.warn(f"I cannot manage {target.mention}")
			if perms.manage_channels:
				return await ctx.warn(f"I cannot manage {target.mention}")	
			if not ctx.author == ctx.guild.owner:
				if target.top_role.position > ctx.author.top_role.position:
					return await ctx.warn(f"You cannot manage {target.mention}")	

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS lockdown(guildid INTEGER UNIQUE, channels)"
				)

				total = len([c for c in ctx.guild.channels if c.overwrites_for(target).send_messages is not False and not isinstance(c, discord.CategoryChannel)])

				locked_list = []

				if not total:
					return await ctx.warn(f"All **channels** are already locked for {target.mention}.")

				for c in ctx.guild.channels:
					if isinstance(c, Union[discord.ForumChannel, discord.Thread]):
						return await c.edit(locked=True, archived=True)
					overwrite = c.overwrites_for(target)
					if overwrite.send_messages is None or overwrite.send_messages is True and not isinstance(c, discord.CategoryChannel):

						overwrite.send_messages = False
						await c.set_permissions(target=target, overwrite=overwrite, reason=f"Lockdown executed by {ctx.author}")

						locked_list.append(c.id)
				
				if not locked_list:
					return await ctx.warn(f"Could not lock any **channels** for {target.mention}.")

				cur = await cursor.execute(
					"SELECT * FROM lockdown WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if row:
					if row[1]:
						data = json.loads(row[1])
						for ch in data and ch not in data:
							locked_list.append(ch)

				await db.execute(
					"REPLACE INTO lockdown(guildid, channels) VALUES ($1, $2)",
					ctx.guild.id, json.dumps(locked_list),
				)
				await db.commit()

				await ctx.approve(f"Locked `{len(locked_list)}/{total}` **channels** for {target.mention}.")


	@server.command(
			name="unlockdown",
			description="Unlocks every channel in the server.",
			brief="unlockdown @member lol",
	)
	async def unlockdown(self, ctx: StealContext, target:Optional[discord.Role], reason: Optional[str] = "No reason."):

		reason += ' | Unlockdown executed by {}'.format(ctx.author)
		if target is None: target = ctx.guild.default_role

		if isinstance(target, discord.Role):
			perms = target.permissions
			if target.position > ctx.guild.me.top_role.position:
				return await ctx.warn(f"I cannot manage {target.mention}.")
			if perms.manage_channels:
				return await ctx.warn(f"I cannot manage {target.mention}.")			
			if not ctx.author == ctx.guild.owner:
				if target.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")		
										
		if isinstance(target, discord.Member):
			perms = target.guild_permissions
			if target == ctx.guild.owner:
				return await ctx.warn("You cannot manage the server owner.")
			if target.top_role.position > ctx.guild.me.top_role.position:
				return await ctx.warn(f"I cannot manage {target.mention}")
			if perms.manage_channels:
				return await ctx.warn(f"I cannot manage {target.mention}")	
			if not ctx.author == ctx.guild.owner:
				if target.top_role.position > ctx.author.top_role.position:
					return await ctx.warn(f"You cannot manage {target.mention}")	

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS lockdown(guildid INTEGER UNIQUE, channels)"
				)

				cur = await cursor.execute(
					"SELECT * FROM lockdown WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn(f"All **channels** are already unlocked for {target.mention}.")
				
				unlocked = 0
				ls = []
				if row[1]:
					ls = json.loads(row[1])
				print(ls)
				locked = len(ls)

				if not ls:
					await db.execute(
						"DELETE FROM lockdown WHERE guildid = $1",
						ctx.guild.id,
					)
					await db.commit()
					return await ctx.warn(f"Could not unlock any **channels** for {target.mention}.")

				for c in ls:

					channel = ctx.guild.get_channel(c)
					if channel:
						print(channel.name)
						overwrite = channel.overwrites_for(target)

						overwrite.send_messages = None
						await channel.set_permissions(target=target, overwrite=overwrite, reason=f"Unlockdown executed by {ctx.author}")

						unlocked += 1
						ls.remove(c)
						await asyncio.sleep(0.5)
					else:
						ls.remove(c)
						return

				if ls:
					await db.execute(
						"REPLACE INTO lockdown(guildid, channels) VALUES ($1, $2)",
						ctx.guild.id, json.dumps(ls),
					)
					await db.commit()
				if not ls:
					await db.execute(
						"DELETE FROM lockdown WHERE guildid = $1",
						ctx.guild.id,
					)
					await db.commit()

				await ctx.approve(f"Unlocked `{unlocked}/{locked}` **channels** for {target.mention}.")

		#overwrite.send_messages = False
		#await channel.set_permissions(target=target, overwrite=overwrite, reason=reason)
		#await ctx.approve(f"Locked {channel.mention} for {target.mention} - **{reason.split(' |')[0]}**")



	@server.command(
			name='icon',
			description='Changes or gets server icon without args.',
			brief="server icon [image]",
			aliases=['pfp', 'logo'],
	)
	@has_permissions(manage_guild=True)
	@bot_has_guild_permissions(manage_guild=True)
	@guild_only()
	async def servericon(self, ctx: StealContext, image:Optional[discord.Attachment] = None) -> None:

		if image is not None:

			bytes_image = await image.read()
			await ctx.guild.edit(icon=bytes_image, reason=f'Updated icon | Executed by {ctx.author}')
			return await ctx.approve(f"Updated guild icon.")
		elif ctx.guild.icon:

			avatarbytes = await ctx.guild.icon.read()

			return await ctx.reply(embed=discord.Embed(
				title=f"{ctx.guild}'s icon",
				url=ctx.guild.icon.url,
				color=await self.bot.dominant_color(avatarbytes)
			).set_image(
				url=ctx.guild.icon.url
				).set_author(
					name=f"{ctx.author}",
					url=ctx.guild.icon.url,
					icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
				)
			)
		else:
			return await ctx.deny(f"Missing argument `image`")

	@server.command(
			name='splash',
			description='Changes or gets server splash without args.',
			brief="server splash [image]",
	)
	@has_permissions(manage_guild=True)
	@bot_has_guild_permissions(manage_guild=True)
	@guild_only()
	async def serversplash(self, ctx: StealContext, image:Optional[discord.Attachment] = None) -> None:

		if image is not None:
			bytes_image = await image.read()

			await ctx.guild.edit(splash=bytes_image, reason=f'Updated splash | Executed by {ctx.author}')
			return await ctx.approve("Updated guild splash.")
		elif ctx.guild.splash:

			avatarbytes = await ctx.guild.splash.read()

			return await ctx.reply(embed=discord.Embed(
				title=f"{ctx.guild}'s splash",
				url=ctx.guild.splash.url,
				color=await self.bot.dominant_color(avatarbytes)
			).set_image(
				url=ctx.guild.splash.url
				).set_author(
					name=f"{ctx.author}",
					url=ctx.guild.icon.url,
					icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
				)
			)
		else:
			return await ctx.deny(f"Missing argument `image`")

	@server.command(
			name='banner',
			brief="server banner [image]",
			description='Changes or gets server banner without args.'
	)
	@has_permissions(manage_guild=True)
	@bot_has_guild_permissions(manage_guild=True)
	@guild_only()
	async def serverbanner(self, ctx: StealContext, image:Optional[discord.Attachment] = None) -> None:

		if image is not None:
			bytes_image = await image.read()

			await ctx.guild.edit(banner=bytes_image, reason=f'Updated banner | Executed by {ctx.author}')
			return await ctx.approve("Updated guild banner.")

		elif ctx.guild.banner:

			avatarbytes = await ctx.guild.banner.read()

			return await ctx.reply(embed=discord.Embed(
				title=f"{ctx.guild}'s banner",
				url=ctx.guild.banner.url,
				color=await self.bot.dominant_color(avatarbytes)
			).set_image(
				url=ctx.guild.banner.url
				).set_author(
					name=f"{ctx.author}",
					url=ctx.guild.icon.url,
					icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
				)
			)
		else:
			return await ctx.deny(f"Missing argument `image`")

	@command(
			name="members",
			brief="members",
			description='Server members.'
	)
	@guild_only()
	async def members(self, ctx: StealContext) -> None:

		members = [mem for mem in ctx.guild.members if not mem.bot]
		bots = [mem for mem in ctx.guild.members if mem.bot]


		if not members:
			return await ctx.warn(f"There are no members in this server.")
			

		count = 0
		embeds = []
		
		entries = [
			f"`{i}` {b.mention} (`{b}`)"
			for i, b in enumerate(members, start=1)
		]

		l = 5

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Members (`{len(entries)}`)",
			description=f"There are `{len(bots)}` bots, `{len(members)}` users and `{len(members)-len(bots)}` total members.\n\n"
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Members (`{len(entries)}`)",
					description=f"There are `{len(bots)}` bots, `{len(members)}` users and `{len(members)-len(bots)}` total members.\n\n"
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)

	@command(
			name="membercount",
			description='Server members.',
			brief="membercount",
			aliases=['mc']
	)
	@guild_only()
	async def membercount(self, ctx: StealContext) -> None:

		humans = [mem for mem in ctx.guild.members if not mem.bot]
		bots = [bot for bot in ctx.guild.members if bot.bot]

		await ctx.send(
			embed=discord.Embed(
				title=f"{ctx.guild.name}'s statistics ({len(humans)})",
				description=f""">>> **humans** - {len(humans)}
							**bots** - {len(bots)}
							**total** - {len(humans + bots)}
							""",
				color=Colors.BASE_COLOR
			).set_author(
				name=ctx.author,
				icon_url=ctx.author.display_avatar
			)
		)

	@command(
		name="roles",
		aliases=["rolelist"],
		brief="roles",
		desciption="Lists server roles."
	)
	@guild_only()
	async def roles(self, ctx: StealContext):
	
		roles = ctx.guild.roles[::-1]

		count = 0
		embeds = []

		if not roles:
			return await ctx.deny("There are no roles in this guild.")
		
		entries = [
			f"`{i}` {b.mention} (`{b.name}`)"
			for i, b in enumerate(roles, start=1) if not i == ctx.guild.default_role
		]

		l = 10

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Roles ({len(entries)})",
			description=""
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Roles ({len(entries)})",
					description=""
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)
				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)

	@command(
		name="emojis",
		aliases=["emojilist"],
		brief="emojis",
		desciption="Lists server emojis."
	)
	@guild_only()
	async def emojis(self, ctx: StealContext):
	
		emojis = ctx.guild.emojis

		count = 0
		embeds = []

		if not emojis:
			return await ctx.deny("There are no emojis in this guild.")
		
		entries = [
			f"`{i}` {b} (`{b.name}`)"
			for i, b in enumerate(emojis, start=1)
		]

		l = 10

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Emojis (`{len(entries)}`)",
			description=""
		).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == l:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Emojis (`{len(entries)}`)",
					description=""
				).set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				)

				count = 0
		
		if count > 0:
			embeds.append(embed.set_footer(
					icon_url=self.bot.user.display_avatar.url or None,
					text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
				))
		
		await ctx.paginate(embeds)

async def setup(bot):
	await bot.add_cog(Info(bot))
