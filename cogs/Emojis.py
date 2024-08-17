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

from managers.interaction import PatchedInteraction
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


class Emojis(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.ctx_menu = discord.app_commands.ContextMenu(
			name="Jumbo",
			callback=self.stickerenlarge

		)
		self.bot.tree.add_command(self.ctx_menu)
		

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

	@emoji.command(
			name="delete",
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

	@guild_only()
	async def stickerenlarge(self, interaction: PatchedInteraction, message: discord.Message):

		if message.stickers:
			for sticker in message.stickers:
				await interaction.response.send_message(embed=
					discord.Embed(
						title=f"{sticker.name}",
						color=Colors.BASE_COLOR
					).set_image(
						url=sticker.url
					).set_author(
						name=interaction.user,
						icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
					)
				)
		else:
			await interaction.warn("There are no stickers in that message.")

async def setup(bot):
	await bot.add_cog(Emojis(bot))
