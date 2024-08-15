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
import math
from aiofiles import open as aio_open

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
			usage="members",
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
			name='hide',
			description='Hides a channel from a user/role.',
			usage='channel hide <channel> <user/role>',
			aliases=["remove"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def hidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Role, discord.Member]] = None):
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.view_channel is None or perms.view_channel is True:
			perms = target.guild_permissions
			if isinstance(target, discord.Role):
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	

			overwrite = channel.overwrites_for(target)
			overwrite.view_channel = False
			await channel.set_permissions(target=target, overwrite=overwrite, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Hidden {channel.mention} from {target.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already hidden for {target.mention}.")

	@managechannels.command(
			name='reveal',
			description='Reveals a channel to a user/role.',
			usage='channel reveal <channel> <user/role>',
			aliases=["add", "show"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def revealchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None, target: Optional[Union[discord.Member, discord.Role]] = None):
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.view_channel is False:
			perms = target.guild_permissions
			if isinstance(target, discord.Role):
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	
		
			overwrite = channel.overwrites_for(target)
			overwrite.view_channel = None
			await channel.set_permissions(target=target, overwrite=overwrite, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Revealed {channel.mention} to {target.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already visible to {target.mention}.")

	@managechannels.command(
			name='rename',
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

	@command(
			name='lock',
			description='Locks a channel.',
			usage='channel lock <channel> <user/role>'
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def lockchannel(self, ctx: StealContext, reason:Optional[str] = "No reason.", channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.send_messages is None or perms.send_messages is True:
			perms = target.guild_permissions
			if isinstance(target, discord.Role):
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	


			overwrite = channel.overwrites_for(target)
			overwrite.send_messages = False
			await channel.set_permissions(target=target, send_messages=False, reason=reason)
			await ctx.approve(f"Locked {channel.mention} for {target.mention} - **{reason.split(' |')[0]}**")
		else:
			await ctx.deny(f"{channel.mention} is already locked for {target.mention}.")

	@command(
			name='unlock',
			description='Unlocks a channel.',
			usage='channel unlock <channel> <user/role>'
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def unlockchannel(self, ctx: StealContext, reason:Optional[str] = "No reason.", channel:Optional[discord.abc.GuildChannel] = None):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.send_messages is False:
			perms = target.guild_permissions
			if isinstance(target, discord.Role):
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	

			overwrite = channel.overwrites_for(target)
			overwrite.send_messages = None
			await channel.set_permissions(target=target, overwrite=overwrite, reason=reason)
			await ctx.approve(f"Unlocked {channel.mention} - **{reason.split(' |')[0]}**.")
		else:
			await ctx.deny(f"{channel.mention} is already unlocked for {target.mention}.")			

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
		await ctx.approve(f'{f"Set {channel.mention}s slowmode to `{time}`" if int(seconds) > 0 else f"Removed {channel}s slowmode."}')

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
			usage="emoji add <attachment/emoji> <name>",
			aliases=['create', 'steal', 'rob'])
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojiadd(self, ctx: StealContext, emoji:Union[discord.Attachment, discord.PartialEmoji], *, emoji_name:Optional[str]=None) -> None:
		try:
			if isinstance(emoji, discord.Attachment):

				if not emoji_name: emoji_name = emoji.filename.split(".")[0]


				emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

				return await ctx.approve(f"Created emoji {emoji}")
			else:

				if not emoji_name: emoji_name = emoji.name


				emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

				return await ctx.approve(f"Stole emoji {emoji}")		

		except:
			return await ctx.deny(f"Could not create emoji {emoji_name}")

	@command(
		name="roles",
		aliases=["rolelist"],
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
		

	@command(
			name="info",
			aliases=["ei"],
			description="Gives emoji info."
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

	@emoji.command(
			name="zip",
			description="Zips all server emojis and sends it.",
			usage="emoji zip"
	)
	@guild_only()
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

	@command(
			name="enlarge", 
			aliases=["download", "e", "jumbo"]
	)
	@guild_only()
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
		def guns(user:discord.Member):
			if isinstance(user, discord.Member):
				has_emote_status = any([a.emoji.is_custom_emoji() for a in user.activities if getattr(a, 'emoji', None)])
 
				if not user.bot:
					return any([user.display_avatar.is_animated(), has_emote_status, user.premium_since, user.guild_avatar, user.banner])
		
		nhavers_ = [mem for mem in ctx.guild.members if guns(mem)]

		if not nhavers_:
			return await ctx.warn(f"There are no premium users in this server.")
			

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
			usage='invites',
			aliases=['invs']
	)
	@guild_only()
	async def invites(self, ctx: StealContext) -> None:
		invites = await ctx.guild.invites() or []
	
		if ctx.guild.vanity_url:
			invites.append(ctx.guild.vanity_url_code)

		count = 0
		embeds = []

		if not invites:
			return await ctx.deny("There are no invites to this guild.")

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
			usage='boosters'
	)
	@guild_only()
	async def boosters(self, ctx: StealContext) -> None:
		boosters = [sub for sub in ctx.guild.premium_subscribers]

		if not boosters:
			return await ctx.warn(f"There are no boosters in this server.")
			

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


async def setup(bot):
	await bot.add_cog(Utility(bot))