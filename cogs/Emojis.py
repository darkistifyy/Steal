from __future__ import print_function, annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
from discord.ui import *
from sklearn import *
import asyncio
import requests
from PIL import Image
import aiohttp
from tools.bytesio import compress_image

from managers.interaction import PatchedInteraction
from tools.Steal import Steal
from managers.context import StealContext

import typing
from io import BytesIO
from typing import List, Optional, Union
from tools.Config import Colors, Emojis
from tools.View import UrlView
import zipfile

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

import re
from typing import Generator, Union, Optional

import discord
from discord.ext import commands

from managers.context import StealContext

class Emojis(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = "Manage server emojis + stickers."
		
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
			aliases=['create', 'steal', 'rob', 'yoink'])
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojiadd(self, ctx: StealContext, emoji:Union[discord.Attachment, discord.PartialEmoji], *, emoji_name:Optional[str]=commands.param(default=Author, displayed_default=None)) -> None:
		try:
			if isinstance(emoji, discord.Attachment):

				if not emoji_name: emoji_name = emoji.filename.split(".")[0]


				emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

				return await ctx.approve(f"Created [**emoji**]({emoji.url}) {emoji}")
			else:

				if not emoji_name: emoji_name = emoji.name


				emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

				return await ctx.approve(f"Stole [**emoji**]({emoji.url}) - {emoji}")		

		except:
			return await ctx.deny(f"Could not create emoji - {emoji_name}")

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
				await ctx.guild.delete_emoji(emoji, reason=f"Executed by {ctx.author}")

				return await ctx.approve(f"Deleted that **emoji**")
			else:
				return await ctx.warn(f"That [**emoji**]({emoji.url}) is not from this server.")
		except:
			return await ctx.deny(f"Could not delete [**emoji**]({emoji.url})")
	
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
				await emoji.edit(name=f"{name}", reason=f"Executed by {ctx.author}")
				
				return await ctx.approve(f"Renamed [**{emoji}**]({emoji.url}) to **{name}**")
			else:
				return await ctx.warn(f"That [**emoji**]({emoji.url}) is not from this server.")
		except:
			return await ctx.deny(f"Could not rename that [**emoji**]({emoji.url})")				

	@emoji.command(
			name="zip",
			description="Zips all server emojis.",
			aliases=["archive"]
	)
	async def sticker_zip(self, ctx: StealContext):

		async with ctx.typing():
			buff = BytesIO()
			with zipfile.ZipFile(buff, "w") as zip:
				for emoji in ctx.guild.emojis:
					zip.writestr(f"{emoji.name}.png", data=await emoji.read())

			buff.seek(0)
			await ctx.send(file=discord.File(buff, filename=f"emojis-{ctx.guild.name}.zip"))

	@emoji.command(
			name="enlarge",
			description="Enlarges an emoji and sends the image.",
			aliases=["download", "e", "jumbo"]
	)
	async def emojienlarge(self, ctx: StealContext, emoji: discord.PartialEmoji):

		if isinstance(emoji, discord.PartialEmoji):
			return await ctx.reply(
				embed=discord.Embed(
					title=f"{emoji.name} image",
					url=emoji.url,
					color=Colors.BASE_COLOR,
				).set_image(
					url=emoji.url
				).set_author(
					name=ctx.author,
					icon_url=ctx.author.display_avatar.url
				),
			)

	@group(
			name="sticker",
			description="Manage stickers."
	)
	async def stickers(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `sticker`.')

	@stickers.command(
		name="create", 
		aliases=["add", "yoink", "steal"],
		description="Adds a sticker."
	)
	@has_guild_permissions(manage_expressions=True)
	@bot_has_guild_permissions(manage_expressions=True)
	async def addsticker(self, ctx: StealContext, name:Optional[str] = commands.param(default=None, displayed_default=None)):

				

				

		if len(ctx.guild.stickers) >= ctx.guild.sticker_limit:
			return await ctx.warn(
				"This server does not have space for new stickers."
			)

		if not ctx.message.stickers and not ctx.message.attachments:	
			return await ctx.warn("Missing argument **sticker/attachment/url**.")

		sticker = [sticker for sticker in ctx.message.stickers or ctx.message.attachments]

		if name is None: name = sticker[0].name if ctx.message.stickers else sticker[0].filename.split(".")[0]

		file = discord.File(fp=BytesIO(await sticker[0].read()))
		stick = await ctx.guild.create_sticker(
			name=name,
			description=name,
			emoji="skull",
			file=file,
			reason=f"Executed by {ctx.author}",
		)
		return await ctx.approve(
			f"Added [**sticker**]({stick.url}) with the name - **{name}**"
		)

	@stickers.command(
			name="delete", 
			description="Deletes a sticker.",
	)
	@has_guild_permissions(manage_expressions=True)
	@bot_has_guild_permissions(manage_expressions=True)
	async def stickerdelete(self, ctx: StealContext):

		if not ctx.message.stickers:
			return await ctx.warn("Missing argument **sticker**.")
		
		sticker = [sticker.id for sticker in ctx.message.stickers]

		sticker = await ctx.guild.fetch_sticker(sticker[0])

		await sticker.delete(reason=f"Executed by {ctx.author}")
		return await ctx.approve("Deleted that **sticker**")

	@stickers.command(
			name='rename',
			description="Renames a sticker."
	)
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickerrename(self, ctx:StealContext, name:str) -> None:
		if not ctx.message.stickers: return await ctx.warn(f"Missing argument **sticker**.")
		sticker = [sticker for sticker in ctx.message.stickers]
		try:
			if sticker[0].id in [sticker.id for sticker in ctx.guild.stickers]:
				sticker = await ctx.guild.fetch_sticker(sticker[0].id)
				await sticker.edit(name=f"{name}", reason=f"Executed by {ctx.author}")
				
				return await ctx.approve(f"Renamed [**sticker**]({sticker.url}) to **{name}**")
			else:
				return await ctx.warn(f"That [**sticker**]({sticker[0].url}) is not from this server.")
		except:
			return await ctx.deny(f"Could not rename that [**sticker**]({sticker.url})")				


	@stickers.command(
			name="zip",
			description="Zips all server emojis.",
			aliases=["archive"]
	)
	@has_permissions(manage_expressions=True)
	@bot_has_guild_permissions(manage_expressions=True)
	async def stickerzip(self, ctx: StealContext):

		async with ctx.typing():
			buff = BytesIO()
			with zipfile.ZipFile(buff, "w") as zip:
				for sticker in ctx.guild.stickers:
					zip.writestr(f"{sticker.name}.png", data=await sticker.read())

			buff.seek(0)
			await ctx.send(file=discord.File(buff, filename=f"stickers-{ctx.guild.name}.zip"))

	@stickers.command(
			name="enlarge",
			description="Enlarges a sticker and sends the image.",
			aliases=["download", "e", "jumbo"]
	)
	async def stickerenlarge(self, ctx: StealContext):

		if not ctx.message.stickers:
			return await ctx.warn("Missing argument **sticker**.")
		
		sticker = [sticker for sticker in ctx.message.stickers]

		return await ctx.reply(
			embed=discord.Embed(
				title=f"{sticker[0].name} image",
				url=sticker[0].url,
				color=Colors.BASE_COLOR,
			).set_image(
				url=sticker[0].url
			).set_author(
				name=ctx.author,
				icon_url=ctx.author.display_avatar.url
			),
		)
	
	@stickers.command(
			name="tag",
			description="Tags all stickers with your vanity invite.",
			aliases=["vanity"]
	)
	async def stickertag(self, ctx: StealContext):

		if not ctx.guild.vanity_url_code:
			return await ctx.warn("This guild does not have a vanity url.")

		tag = f"[.gg/{ctx.guild.vanity_url_code}]"
		
		amount = 0
		total = len(ctx.guild.stickers)
		async with ctx.typing():
			for sticker in ctx.guild.stickers:
				if tag not in sticker.name:
					try:
						name = sticker.name
						tagged = f"{name} {tag}"
						await sticker.edit(name=tagged)
						amount += 1
						await asyncio.sleep(0.5)
					except:
						pass
				else:
					total -= 1

		return await ctx.approve(f"Tagged {amount}/{total} non-tagged stickers successfully.")



async def setup(bot):
	await bot.add_cog(Emojis(bot))
