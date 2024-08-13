from __future__ import print_function

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import asyncio
from discord.ui import *
import base64
import requests
import psutil
from sklearn import *
import scipy.cluster
import sys
import unicodedata
import aiohttp
import mimetypes
import functools
import io
import zipfile


from tools.Steal import Steal
from tools.EmbedBuilder import EmbedBuilder, EmbedScript
from managers.context import StealContext
from tools.View import DownloadAsset

from typing import List, Optional, Union
from tools.Config import Colors, Emojis

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from tools.bytesio import dom_color, caption_image

from io import BytesIO
from sklearn.cluster import KMeans
from skimage.transform import rescale

from tools.EmbedBuilder import EmbedBuilder, EmbedScript

import binascii
import struct

class ChannelDeleteConfirm(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@button(label="Confirm", emoji="✅", style=discord.ButtonStyle.green, custom_id="channeldeleteconfirm")
	async def channeldeleteconfirm(self,interaction:discord.Interaction, button:Button):
		await interaction.response.defer()
		for button in self.children:
			button.disabled=True
			await interaction.message.edit(view=self)

		await interaction.channel.delete(
			reason=f'Executed by {interaction.user}'
		)
	@button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, custom_id="channeldeletecancel")
	async def channeldeletecancel(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer()
		for button in self.children:
			button.disabled=True
			return await interaction.message.edit(embed=discord.Embed(description=f"{Emojis.DENY} You have cancelled the deletion of {interaction.channel.mention}", color=Colors.DENY_COLOR), view=self)

class Utility(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot

	@command(
			name='embed',
			description='Sends an embed.',
			aliases=['em'],
			usage='embed {title:fart}{description:this is a description}')
	async def embedsend(self, ctx: StealContext, *, message:str) -> None:
		
		processed_message = EmbedBuilder.embed_replacement(ctx.author, message)
		content, embed, view = await EmbedBuilder.to_object(processed_message)
		await ctx.send(content=content, embed=embed, view=view)

	@command(
			name="embedcode",
			descrtiption="Sends code for an embed.",
			aliases=["ec"],
			usage='ec <reply to a message>'
	)
	async def embedcode(self, ctx: StealContext) -> None:
		
		if not ctx.message.reference:
			return await ctx.warn(f"Respond to a message to fetch the embed code.")
		ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
		embed_code = EmbedBuilder.copy_embed(self, ref)
		await ctx.send(f"```{embed_code}```")


	@command(
			name='dominant',
			aliases=["hex", "imagehex"]
	)
	async def dominant(self, ctx: StealContext, image: discord.Attachment):

		color = hex(await self.bot.dominant_color(image.url))[2:]
		hex_info = await self.bot.session.get_json(
			"https://www.thecolorapi.com/id", params={"hex": color}
		)
		hex_image = f"https://singlecolorimage.com/get/{color}/200x200"
		embed = (
			discord.Embed(color=int(color, 16))
			.set_author(icon_url=hex_image, name=hex_info["name"]["value"])
			.set_thumbnail(url=hex_image)
			.add_field(name="RGB", value=f'`{hex_info["rgb"]["value"]}`')
			.add_field(name="HEX", value=f'`{hex_info["hex"]["value"]}`')
		)

		await ctx.send(embed=embed)

	@command(
			name="avatar",
			description='Gets someones avatar.',
			aliases=['av', 'pfp'],
			usage='avatar [@user]'
	)
	async def avatar(self, ctx: StealContext, member:Optional[discord.User]) -> None:
		if not member:member=ctx.author
		if not member.display_avatar:
			return await ctx.deny(f"**{member}** does not have an avatar.")

		avatarbytes = await member.display_avatar.read()
		dominant_color = dom_color(avatarbytes)

		from isHex import isHex

		if isHex(dominant_color):
			rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))
			await ctx.reply(embed=discord.Embed(title=f"{member.display_name}'s avatar", url=member.display_avatar.url, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])).set_image(url=member.display_avatar.url))
		

	@command(
			name="banner",
			description='Gets someones avatar.',
			usage='avatar [@user]'
	)
	async def banner(self, ctx: StealContext, member:Optional[discord.User]) -> None:
		if not member:member=ctx.author
		user = await self.bot.fetch_user(member.id)
		if user.banner:

			bannerbytes = await user.banner.read()
			dominant_color = dom_color(bannerbytes)

			from isHex import isHex

			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))
				await ctx.reply(embed=discord.Embed(title=f"{user.display_name}'s banner", url=user.banner.url, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])).set_image(url=user.banner))
		else:
			return await ctx.send(embed=discord.Embed(
				title=f"{member.display_name}'s banner color: {user.accent_color}", color=user.accent_color
				))

	@command(
			name="members",
			description='Server members.'
	)
	@guild_only()
	async def members(self, ctx: StealContext) -> None:
		await ctx.reply(embed=discord.Embed(description=f'There are `{len(ctx.guild.members)-len([i for i in ctx.guild.members if i.bot])}` members excluding bots.', color=Colors.BASE_COLOR).add_field(
			name='Members:',
			value=f'`{len(ctx.guild.members)}`'
		).add_field(
			name='Bots:',
			value=f'`{len([i for i in ctx.guild.members if i.bot])}`'
		))

	@group(
			name="channel",
			description="Manage channels."
	)
	async def managechannels(self, ctx: StealContext) -> None:
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `channel`.')

	@managechannels.command(
			name='delete',
			description='Deletes a channel.',
			usage='channel delete <channel>'
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def deletechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None) -> None:
		if not channel or channel == ctx.channel:
			bs = "\'"
			return await ctx.warn(f'{f"I couldn{bs}t find a channel with those parameters" if not channel else ""}. Would you like to delete {ctx.channel.mention}?', view=ChannelDeleteConfirm())
			
		
		if channel in ctx.guild.channels:
			await channel.delete(reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Deleted {channel.name}")
			
		await ctx.warn(f'{channel} is not a valid channel.')

	@managechannels.command(
			name='create',
			description='Creates a channel.',
			usage='channel create <name>'
	)
	@cooldown(2, 5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def createchannel(self, ctx: StealContext, name:Optional[str]) -> None:
		channel = await ctx.guild.create_text_channel(name=name if name else "channel", reason=f'Executed by {ctx.author}')
		await ctx.approve(f'Created {channel.mention}.')

	@managechannels.command(
			name="remove",
			description="Removes a member from a channel.",
			usage=f'channel remove <user> <channel'
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def removechannel(self, ctx: StealContext, member:discord.Member, channel: Optional[discord.abc.GuildChannel]):
		if channel is None: channel = ctx.channel	
		if member in channel.members:
			await channel.set_permissions(target=member, view_channel=False, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Removed {member.mention} from {channel.mention}.")
		else:	
			await ctx.deny(f"{member.mention} is not a member of {channel.mention}")

	@managechannels.command(
			name="add",
			description="Adds a member to a channel.",
			usage=f'channel add <user> <channel'
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def addchannel(self, ctx: StealContext, member:discord.Member, channel: Optional[discord.abc.GuildChannel]):
		if channel is None: channel = ctx.channel	
		if member not in channel.members:
			await channel.set_permissions(target=member, view_channel=True, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Added {member.mention} to {channel.mention}.")
		else:	
			await ctx.deny(f"{member.mention} is already a member of {channel.mention}.")

	@managechannels.command(
			name='hide',
			description='Hides a channel from @everyone.',
			usage='channel hide <channel>'
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def hidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None):
		if channel is None: channel = ctx.channel	
		perms = channel.overwrites_for(ctx.guild.default_role)
		if perms.view_channel is None or perms.view_channel is True:
			await channel.set_permissions(ctx.guild.default_role, view_channel=False, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Hidden {channel.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already hidden.")

	@managechannels.command(
			name='reveal',
			description='Reveals a channel to @everyone.',
			usage='channel reveal <channel>'
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def revealchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None):
		if channel is None: channel = ctx.channel	
		perms = channel.overwrites_for(ctx.guild.default_role)
		if not perms.view_channel:
			await channel.set_permissions(ctx.guild.default_role, view_channel=True, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Revealed {channel.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already visible.")

	@managechannels.command(name='rename',
			description='Renames a channel.',
			usage='channel rename <channel> <name>'
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def renamechannel(self, ctx: StealContext, name:str, channel:Optional[discord.abc.GuildChannel]) -> None:
		if not channel:channel=ctx.channel
		try:
			await asyncio.wait_for(channel.edit(name=name, reason=f'Executed by {ctx.author}'), timeout=2)
			channel = await ctx.guild.fetch_channel(channel.id)
			return await ctx.approve(f'Renamed {channel.mention} to `{channel.name}`.')
		except asyncio.TimeoutError:
			return await ctx.warn(f'Could not rename {channel.mention}, bot is ratelimited.')

		except Exception as e:
			return await ctx.deny(f'Error:\n```{e}```')

	@command(name='lock',
			description='Locks a channel.',
			usage='channel lock <channel>'
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def lockchannel(self, ctx: StealContext, reason:Optional[str] = "No reason.", channel:Optional[discord.abc.GuildChannel] = None):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel	
		perms = channel.overwrites_for(ctx.guild.default_role)
		if perms.send_messages is None or perms.send_messages is True:
			await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
			await ctx.approve(f"Locked {channel.mention} - **{reason.split(' |')[0]}**.")
		else:
			await ctx.deny(f"{channel.mention} is already locked.")

	@command(name='unlock',
		  description='Unlocks a channel.',
		  usage='channel unlock <channel>'
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def unlockchannel(self, ctx: StealContext, reason:Optional[str] = "No reason.", channel:Optional[discord.abc.GuildChannel] = None):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel	
		perms = channel.overwrites_for(ctx.guild.default_role)
		if perms.send_messages is False:
			await channel.set_permissions(ctx.guild.default_role, send_messages=None, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Unlocked {channel.mention} - **{reason.split(' |')[0]}**.")
		else:
			await ctx.deny(f"{channel.mention} is already unlocked.")			

	@command(name="slowmode",
		  description="Set a channel slowmode",
		  usage='slowmode 10s [channel]',
		  aliases=['sm']
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	async def slowmode_set(self, ctx:StealContext, time, channel:Optional[discord.abc.GuildChannel]) -> None:
		if not channel:channel=ctx.channel
		def time_conv(time):
			try:
				return int(time[:-1]) * time_convert[time[-1]]
			except:
				return time
		seconds = time_conv(time.lower())
		await channel.edit(slowmode_delay=seconds, reason=f'Executed by {ctx.author}')
		await ctx.approve(f'{f"Set {channel}s slowmode to `{time}`" if int(seconds) > 0 else f"Removed {channel}s slowmode."}')

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

	@command(
			name="serverinfo",
			description="Gives server info.",
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
			name="userinfo",
			description="Gives userinfo.",
			aliases=["ui", "uinfo"],
			usage='userinfo [user]'
	)
	@cooldown(1,15, commands.BucketType.user)
	@guild_only()
	async def userinfo(self, ctx:StealContext, member: Optional[discord.Member]) -> None:

		if not member:member = ctx.author

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


	@group(
			name='server',
			description='Manages server.',
			aliases=['guild']
	)
	async def server(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `server`.')

	@server.command(
			name='icon',
			description='Changes or gets server icon without args.',
			aliases=['pfp', 'logo'],
			usage="server icon <image/attatchment>"
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
			dominant_color = dom_color(avatarbytes)
			from isHex import isHex
			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

			return await ctx.send(embed=discord.Embed(
				title=f"{ctx.guild}'s icon",
				color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])
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
			description='Changes or gets server splash without args.'
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
			dominant_color = dom_color(avatarbytes)
			from isHex import isHex
			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

			return await ctx.send(embed=discord.Embed(
				title=f"{ctx.guild}'s splash",
				color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])
			).set_image(
				url=ctx.guild.splash
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
			dominant_color = dom_color(avatarbytes)
			from isHex import isHex
			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

			return await ctx.send(embed=discord.Embed(
				title=f"{ctx.guild}'s banner",
				color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])
			).set_image(
				url=ctx.guild.banner
				).set_author(
					name=f"{ctx.author}",
					url=ctx.guild.icon.url,
					icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
				)
			)
		else:
			return await ctx.deny(f"Missing argument `image`")

	@group(
			name='emoji',
			description='Manage emojis.'
	)
	async def emoji(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `emoji`.')
	
	@emoji.command(
			name="add",
			description="Adds an emoji.",
			usage="emoji add <attachment> <name>",
			aliases=['create'])
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojiadd(self, ctx: StealContext, emoji:discord.Attachment, *, emoji_name:Optional[str]=None) -> None:
		try:
			if not emoji_name: emoji_name = emoji.filename.split(".")[0]


			emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Created emoji {emoji}")
		except:
			return await ctx.deny(f"Could not create emoji {emoji_name}")

	@emoji.command(
			name="steal",
			usage="emoji steal <emoji> <name>",
			description="Steals an emoji."
	)
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojisteal(self, ctx: StealContext, emoji:discord.PartialEmoji, *, emoji_name:Optional[str]=None) -> None:
		try:
			if not emoji_name: emoji_name = emoji.name


			emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Stole emoji {emoji}")
		except:
			return await ctx.deny(f"Could not Steal emoji {emoji_name}")

	@command(
		name="emojis",
		aliases=["emojilist"],
		desciption="Lists server emojis."
	)
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

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			title=f"Emojis ({len(entries)})",
			description=""
		)

		for entry in entries:
			embed.description += f'{entry}\n'
			count += 1
			
			if count == 5:
				embeds.append(embed)
				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					title=f"Emojis ({len(entries)})",
					description=""
				)
				count = 0
		
		if count > 0:
			embeds.append(embed)
		
		await ctx.paginate(embeds)

	@command(
			name="info",
			aliases=["ei"],
			description="Gives emoji info."
	)
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

	@emoji.command(
			name="zip",
			description="Zips all server emojis and sends it.",
			usage="emoji zip"
	)
	async def emojis_zip(self, ctx: StealContext):

		async with ctx.typing():
			if ctx.guild.emojis:
				buff = BytesIO()
				with zipfile.ZipFile(buff, "w") as zip:
					for emoji in ctx.guild.emojis:
						zip.writestr(
							f"{emoji.name}.{'gif' if emoji.animated else 'png'}",
							data=await emoji.read(),
						)
			else:
				return await ctx.warn("This guild has no emojis.")

		buff.seek(0)
		await ctx.send(file=discord.File(buff, filename=f"emojis-{ctx.guild.name}.zip"))

	@emoji.command(
			name="enlarge", 
			aliases=["download", "e", "jumbo"]
	)
	async def emojienlarge(self, ctx: StealContext, *, emoji: Union[discord.PartialEmoji, str]):

		if isinstance(emoji, discord.PartialEmoji):
			await ctx.send(embed=
				discord.Embed(
					color=Colors.BASE_COLOR
				).set_image(
					url=emoji.url
				).set_author(
					name=ctx.author,
					icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
				)
			)
		else:
			await ctx.warn("That is not a valid emoji.")


	@emoji.command(
			name="delete",
			usage="emoji delete <emoji>",
			description="Deletes an emoji."
	)
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojidelete(self, ctx: StealContext, emoji:discord.PartialEmoji) -> None:
		try:
			if emoji in ctx.guild.emojis:
				await ctx.guild.delete_emoji(emoji)

				return await ctx.approve(f"Deleted emoji {emoji}")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not delete emoji {emoji}")
	
	@emoji.command(
			name='rename',
			usage="emoji rename <emoji> <name>",
			description="Renames an emoji."
	)
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojirename(self, ctx:StealContext, emoji:discord.PartialEmoji, *, name:str) -> None:
		try:
			if emoji in ctx.guild.emojis:
				emoji = await ctx.guild.fetch_emoji(emoji.id)
				await emoji.edit(name=f"{name}")
				
				return await ctx.approve(f"Renamed {emoji} to **{name}**")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not rename emoji {emoji}")				

	@command(
			name='nitrohavers',
			description='Users with nitro.',
			aliases=['nhavers', 'nhs', 'premiumusers'],
			usage="nitrohavers"
	)
	@guild_only()
	async def nhavers(self, ctx: StealContext) -> None:
		nhavers_ = []

		def guns(user:discord.Member):
			if isinstance(user, discord.Member):
				has_emote_status = any([a.emoji.is_custom_emoji() for a in user.activities if getattr(a, 'emoji', None)])
 
				return any([user.display_avatar.is_animated(), has_emote_status, user.premium_since, user.guild_avatar, user.banner])
		def get_nhavers():
			number = 1
			for i in ctx.guild.members:
				if not i.bot:
					if guns(i):
						nhavers_.append(f"`{number}` {i.mention}\n")
						number += 1

		get_nhavers()
		if not nhavers_:
			await ctx.warn(f"There are no premium users in this server.")
			return
		await ctx.send(embed=discord.Embed(title='__Premium users__', description="".join(i for i in nhavers_), color=Colors.BASE_COLOR))

	@command(
			name="boosters",
			description='Users server boosting.',
			usage='boosters'
	)
	@guild_only()
	async def boosters(self, ctx: StealContext) -> None:
		number = 1
		boosters = []
		
		for sub in ctx.guild.premium_subscribers:
			boosters.append(f"`{number}` {sub.mention} - {discord.utils.format_dt(sub.premium_since, style='R')}\n")
			number += 1
			

		if not boosters:
			return await ctx.warn(f"There are no boosters in this server.")        

		embed1 = discord.Embed(title='__Boosters__', description=f''.join(i for i in boosters), color=Colors.BASE_COLOR).set_author(icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None, name=ctx.author)
		await ctx.reply(embed=embed1)        

async def setup(bot):
	await bot.add_cog(Utility(bot))