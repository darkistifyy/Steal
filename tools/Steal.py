from __future__ import annotations

import importlib
from io import BytesIO
import jishaku
import logging
import asyncpg
import pathlib
import asyncio
import aiohttp
import discord
import secrets
import string
import glob
import json
import sys
import os
import re
import glob
import datetime
import time
import colorgram

from PIL import Image

from asyncpg import Pool
from typing import Dict, Union
from collections import defaultdict

from discord.ext import commands
from discord import Message, Embed

from managers.help import StealHelp
from tools.Session import Session
from managers.context import StealContext
from tools.Config import Colors, Emojis
from discord.ext import commands

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()

class Steal(commands.Bot):
	def __init__(self):
		self.errors = Dict[str, commands.CommandError]
		self._uptime = time.time()
		self.session = Session()

		super().__init__(
			command_prefix=[';', 'sudo '],
			help_command=StealHelp(),
			intents=intents,
			allowed_mentions=discord.AllowedMentions(
				everyone=False,
				users=True,
				roles=False,
				replied_user=False
			),
			case_insensitive=True,
			owner_ids=[1182755690071212092, 1039379534409117717],
		)

	async def load_modules(self, dir:str) -> None:
		for module in os.listdir(f'{dir}'):
			if not module.endswith(".py"):return
			try:
				print(module)
				await self.load_extension(f"cogs.{module[:-3]}")
				log.info(f'Loaded module: {module}')
			except commands.ExtensionFailed:
				log.warning(f'Extension failed to load: {module}')
				raise
			except Exception as e:
				log.error(f'Error loading module {module}: {e}')

	async def on_ready(self) -> None:
		log.info(f'Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})')
		log.info(f'Connected to {len(self.guilds)} guilds')
		log.info(f'Connected to {len(self.users)} users')

	async def setup_hook(self) -> None:
		await self.load_modules('cogs')

		from cogs.Tickets import TicketModPanel, TicketClose, TicketCreate

		self.add_view(TicketClose())
		self.add_view(TicketCreate())
		self.add_view(TicketModPanel())
		try:
			print("Jishaku.")
			await self.load_extension("jishaku")
			log.info("Loaded module: Jishaku.")
		except commands.ExtensionFailed:
			log.warning(f'Extension failed to load: Jishaku.')
			raise
		except Exception as e:
			log.error(f'Error loading module Jishaku.: {e}')		

		return await super().setup_hook()

	def humanize_number(self, number: int) -> str:
		suffixes = ['', 'k', 'm', 'b', 't']
		magnitude = min(len(suffixes) - 1, (len(str(abs(number))) - 1) // 3)
		formatted_number = '{:.1f}'.format(number / 10 ** (3 * magnitude)).rstrip('0').rstrip('.')
		return '{}{}'.format(formatted_number, suffixes[magnitude])

	def humanize_time(self, start_time: float) -> str:
		uptime_seconds = abs(time.time() - start_time)
		intervals = (
			('year', 31556952),
			('month', 2629746),
			('day', 86400),
			('hour', 3600),
			('minute', 60),
			('second', 1),
		)

	async def getbyte(self, url: str) -> BytesIO:

		return BytesIO(await self.session.get_bytes(url))

		result = []
		for name, count in intervals:
			value = uptime_seconds // count
			if value:
				uptime_seconds -= value * count
				result.append(f"{int(value)} {name}{'s' if value > 1 else ''}")

		return ', '.join(result)
	
	async def dominant_color(self, url: Union[discord.Asset, str]) -> int:
		if isinstance(url, discord.Asset):
			url = url.url

		img = Image.open(BytesIO(await self.session.get_bytes(url)))
		img.thumbnail((32, 32))

		colors = await asyncio.to_thread(lambda: colorgram.extract(img, 1))
		return discord.Color.from_rgb(*list(colors[0].rgb)).value

	@property
	def uptime(self) -> str:
		return self.humanize_time(self._uptime)
	
	async def on_command_error(self, ctx: StealContext, exception: commands.CommandError) -> None:
		if type(exception) in [commands.CommandNotFound, commands.NotOwner, commands.CheckFailure]: return
		elif isinstance(exception, commands.BadColourArgument):
			return await ctx.warn(f"I was **unable** to find that **color**.")
		elif isinstance(exception, commands.RoleNotFound):
			return await ctx.warn(f"I was unable to find the role **{exception.argument}**.")
		elif isinstance(exception, commands.ChannelNotFound):
			return await ctx.warn(f"I was unable to find the channel **{exception.argument}**")
		elif isinstance(exception, commands.ThreadNotFound):
			return await ctx.warn(f"I was unable to find the thread **{exception.argument}**")
		elif isinstance(exception, commands.BadUnionArgument):
			if discord.Emoji in exception.converters or discord.PartialEmoji in exception.converters:
				return await ctx.warn(f"Invalid **emoji** provided.")
			elif discord.User in exception.converters or discord.Member in exception.converters:
				return await ctx.warn(f"I was unable to find that **member** or the provided **ID** is invalid.")
			return await ctx.warn(f"Could not convert **{exception.param.name}** to **{exception.converters}**")
		elif isinstance(exception, commands.CommandInvokeError):
			if isinstance(exception.original, ValueError):
				return await ctx.warn(exception.original)
			if isinstance(exception, commands.MissingPermissions):
				return await ctx.warn(f"I do not have permissions to do that.")
			elif isinstance(exception.original, aiohttp.ClientConnectorError):
				return await ctx.warn(f"**Failed** to connect to the **URL** - Possibly invalid.")
			elif isinstance(exception.original, aiohttp.ClientResponseError): 
				if exception.original.status == 522:
					return await ctx.warn(f"**Timed out** while requesting data - probably the API's fault")
				return await ctx.warn(f"**API** returned a **{exception.original.status}** status - try again later.")
			elif isinstance(exception.original, discord.Forbidden):
				return await ctx.warn(f"I do not have permission to do that.")
			elif isinstance(exception.original, discord.NotFound):
				return await ctx.warn(f"**Not found** - the **ID** is invalid")
			elif isinstance(exception.original, aiohttp.ContentTypeError):
				return await ctx.warn(f"**Invalid content** - the **API** returned an unexpected response")
			elif isinstance(exception.original, aiohttp.InvalidURL):
				return await ctx.warn(f"The provided **url** is invalid")
			elif isinstance(exception.original, asyncpg.StringDataRightTruncationError):
				return await ctx.warn(f"**Data** is too **long** - try again with a shorter message")
			return await ctx.warn(exception.original)
		elif isinstance(exception, commands.UserNotFound):
			return await ctx.warn("I was unable to find that **member** or the **ID** is invalid")
		elif isinstance(exception, commands.MemberNotFound):
			return await ctx.warn(f"I was unable to find a member with the name: **{exception.argument}**")
		elif isinstance(exception, commands.MissingPermissions):
			return await ctx.warn(f"You're **missing** permission: `{exception.missing_permissions[0]}`")
		elif isinstance(exception, commands.BotMissingPermissions):
			return await ctx.warn(f"I'm **missing** permission: `{exception.missing_permissions[0]}`")
		elif isinstance(exception, commands.GuildNotFound):
			return await ctx.warn(f"I was unable to find that **server** or the **ID** is invalid")
		elif isinstance(exception, commands.BadInviteArgument):
			return await ctx.warn(f"Invalid **invite code** given")
		elif isinstance(exception, commands.UserInputError): 
			return await ctx.warn(f"**Invalid Input Given**: \n`{exception}`")
		elif isinstance(exception, commands.CommandOnCooldown):
			return await ctx.neutral(f"Please wait **{exception.retry_after:.2f} seconds** before using this command again.")
		if isinstance(exception, commands.errors.NotOwner):
			return await ctx.deny(f'You are not an owner of {self.user.mention}.')
		if isinstance(exception, commands.NoPrivateMessage):
			return await ctx.deny(f'This command is not made to be run in **private messages**.')
		if isinstance(exception, commands.ExtensionNotFound):
			return await ctx.warn(f"I'm **unable** to find the cog **{exception.args}**")
		if isinstance(exception, commands.ExtensionNotLoaded):
			return await ctx.warn(f"**{exception.args}** is not **loaded**.")
		if isinstance(exception, commands.MissingPermissions):
			return await ctx.warn(f"I do not have permissions to do that.")
		elif isinstance(exception.original, discord.HTTPException):
			return await ctx.warn(f"**Invalid code**\n```{exception.original}```")

	async def get_context(self, message, *, cls= StealContext):
		return await super().get_context(message, cls=cls)