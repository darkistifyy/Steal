from __future__ import print_function, annotations

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
import os
import zlib

from tools.Steal import Steal
from tools.rtfm import fuzzy
from tools.EmbedBuilder import EmbedBuilder, EmbedScript
from managers.context import StealContext
from tools.View import DownloadAsset

import typing
from typing import List, Optional, Union
from tools.Config import Colors, Emojis
from tools.View import UrlView

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from tools.bytesio import dom_color, caption_image

from io import BytesIO
from sklearn.cluster import KMeans
from skimage.transform import rescale

import binascii
import struct

import re
from typing import Generator, Union, Optional

import discord
from discord.ext import commands

from managers.context import StealContext

from tools.EmbedBuilderUi import EmbedEditor, Embed

class Roles(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		
	@group(name="role", description="Manage roles.")
	async def userrole(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `role`.')

	@userrole.command(
			name='add', 
			description='Adds a role', 
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def roleadd(self, ctx: StealContext, member:discord.Member, role:discord.Role, *, reason: Optional[str] = "No reason.") -> None:
			reason += ' | Executed by {}'.format(ctx.author)
			if member.top_role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny("You do not have permission to manage this users roles.")
			if member.top_role > ctx.guild.me.top_role:
				return await ctx.warn(f'Bot does not have permission to manage this user.')
			if role in member.roles:
				return await ctx.warn(f'{member.mention} already has {role.mention}')
			await member.add_roles(
				role, reason=reason
			)
			return await ctx.approve(f"Added {role.mention} to {member.mention} - {reason.split(' |')[0]}")

	@userrole.command(
			name='remove', 
			description='Removes a role',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def roleremove(self, ctx: StealContext, member:discord.Member, role:discord.Role, reason: Optional[str] = "No reason.") -> None: 
			reason += ' | Executed by {}'.format(ctx.author)
			if member.top_role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f'You do not have permission to manage this users roles.')
			if member.top_role > ctx.guild.me.top_role:
				return await ctx.warn(f'Bot does not have permission to manage this user.')
			if not role in member.roles:
				return await ctx.warn(f'{member.mention} does not have {role.mention}')
			await member.remove_roles(
				role, reason=reason
			)
			return await ctx.approve(f"Removed {role.mention} from {member.mention} - {reason.split(' |')[0]}")

	@userrole.command(
			name='rename',
			description='Renames a role.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def rolerename(self, ctx: StealContext, role:discord.Role, *,name:str) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny('You do not have permission to manage this role.')
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'Bot does not have permission to manage this role.')
		
		try:
			await asyncio.wait_for(role.edit(name=name, reason=f'Executed by {ctx.author}'), timeout=3)
			return await ctx.approve(f"Renamed {role.mention} to **{name}**")

		except asyncio.TimeoutError:
			return await ctx.warn(f'Could not rename {role.mention}, bot is ratelimited.')

	@userrole.command(
			name='addall',
			description='Adds role to all.',
	)
	@cooldown(1,120, commands.BucketType.guild)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleaddall(self, ctx: StealContext, role:discord.Role) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny('You do not have permission to manage this role.')
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'Bot does not have permission to manage this role.')
		mems = len([i for i in ctx.guild.members])
		applied = 0
		failed = 0
		for mem in ctx.guild.members:
			if not role in mem.roles:
				try:
					await mem.add_roles(
						role, reason=f"Mass application | Executed by {ctx.author}"
					)
					applied += 1
				except:
					failed += 1
			else:
				failed += 1        

		embed = discord.Embed(title=f"__Mass Application__",description=f'{Emojis.APPROVE} Role applied: {role.mention}', color=Colors.BASE_COLOR).set_footer(
			icon_url=ctx.author.avatar.url,
			text=f'Command run by {ctx.author} || {ctx.author.id}'
			).add_field(
				name='Successful applications:',
				value=f'`{applied}`',
				inline=False
				).add_field(
					name="Failed applications:",
					value=f'{failed}',
					inline=False
				).add_field(
					name="Server membercount:",
					value=f"{mems}",
					inline=False
				)
		
		await ctx.reply(embed=embed)

	@userrole.command(
			name='removeall',
			description='Removes role from all',
	)
	@cooldown(1,120, commands.BucketType.guild)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleremoveall(self, ctx: StealContext, role:discord.Role) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny('You do not have permission to manage this role.')
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'Bot does not have permission to manage this role.')
		mems = len([i for i in ctx.guild.members])
		removed = 0
		failed = 0
		for mem in ctx.guild.members:
			if role in mem.roles:
				try:
					await mem.remove_roles(
						role, reason=f'Mass removal | Executed by {ctx.author}'
					)
					removed += 1
				except:
					failed += 1
			else:
				failed += 1        

		embed = discord.Embed(title=f"__Mass Removal__",description=f'{Emojis.APPROVE} Role removed: {role.mention}', color=Colors.BASE_COLOR).add_field(
				name='Successful removals:',
				value=f'`{removed}`',
				inline=False
				).add_field(
					name="Failed removals:",
					value=f'{failed}',
					inline=False
				).add_field(
					name="Server membercount:",
					value=f"{mems}",
					inline=False
				)
		await ctx.reply(embed=embed)        

	@userrole.command(
			name='hoist',
			description='Hoists or unhoists a role.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def hoistrole(self, ctx: StealContext, role:discord.Role) -> None:
		if role.hoist is True:
			await role.edit(hoist=False, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Dehoisted {role.mention}.")
		else:
			await role.edit(hoist=True, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Hoisted {role.mention}.")		

	@userrole.command(
			name='color',
			description='Sets a role color.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def colorrole(self, ctx: StealContext, role:discord.Role, hex:Optional[str] = None) -> None:
		if hex is None:
			return await ctx.approve(f"Hex color of {role.mention}: {role.color}")

		import regex as re
		from isHex import isHex, isHexLower, isHexUpper
		
		if role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f'You do not have permission to manage {role.mention}.')

		hex = hex.lstrip("#")
		if isHex(hex):
			rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
			await role.edit(color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]), reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Set {role.mention}'s color to `{hex}`")
		else:
			return await ctx.deny(f"`{hex}` is not a valid hex code.")

	@userrole.command(
			name='icon',
			description='Sets a role icon.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def roleicon(self, ctx: StealContext, role:discord.Role, image:Optional[discord.Attachment] = None) -> None:
		if image is None:
			if role.display_icon:
				if not isinstance(role.display_icon, str):
					avatarbytes = await role.display_icon.read()
					dominant_color = dom_color(avatarbytes)

					from isHex import isHex

					if isHex(dominant_color):
						rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

						return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s icon", url=role.display_icon.url, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])).set_image(url=role.display_icon.url))
				return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s icon: {role.display_icon}", color=Colors.BASE_COLOR))
			else: 
				return await ctx.deny(f"Missing argument `image`")
		else:

			import regex as re
			from isHex import isHex, isHexLower, isHexUpper

			if role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f'You do not have permission to manage {role.mention}.')

			icon = await image.read()

			await role.edit(display_icon=icon, reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Set {role.mention}'s display icon")
	
	@userrole.command(
			name='emoji',
			description='Sets a role emoji.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def roleemoji(self, ctx: StealContext, role:discord.Role, emoji:Optional[str] = None) -> None:
		if emoji is None:
			if role.display_icon:
				if not isinstance(role.display_icon, str):
					avatarbytes = await role.display_icon.read()
					dominant_color = dom_color(avatarbytes)

					from isHex import isHex

					if isHex(dominant_color):
						rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

						return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s icon", url=role.display_icon.url, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])).set_image(url=role.display_icon.url))
				return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s icon: {role.display_icon}", color=Colors.BASE_COLOR))
			else: 
				return await ctx.deny(f"Missing argument `emoji`")
		else:
			import regex as re
			from isHex import isHex, isHexLower, isHexUpper

			if role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f'You do not have permission to manage {role.mention}.')

			if emoji.id:
				icon = await emoji.read()

				await role.edit(display_icon=icon, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Set {role.mention}'s display icon")

			await role.edit(display_icon=emoji, reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Set {role.mention}'s display emoji to {emoji}")

	@userrole.command(
			name='delete',
			description='Deletes a role.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def deleterole(self, ctx: StealContext, role:discord.Role) -> None:
		if role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f'You do not have permission to manage {role.mention}.')

		await role.delete(reason=f'Executed by {ctx.author}')
		return await ctx.approve(f"Deleted  {role.name}")	

	@userrole.command(
			name='create',
			description='Creates a role.',
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def createrole(self, ctx: StealContext, name:Optional[str], hoist:Optional[bool] = False, hex:Optional[str] = None) -> None:
		from isHex import isHex

		rgb = None

		if hex:
			hex = hex.lstrip("#")
			if isHex(hex):
				rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
			else:
				rgb = None

		role = await ctx.guild.create_role(name=name if name else "new role", hoist=hoist, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]) if rgb else None, reason = f"Executed by {ctx.author}")
		await ctx.approve(f"Created role {role.mention}.")


async def setup(bot):
	await bot.add_cog(Roles(bot))