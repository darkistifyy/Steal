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
import numpy as np
import scipy.cluster
import scipy.cluster.vq
import binascii
from discord.ext import tasks, commands
import random
from events.Loops import snipe_delete, reminder_task, change_status

from PIL import Image

from num2words import num2words
from asyncpg import Pool
from typing import Dict, Union
from collections import defaultdict
from humanize import precisedelta

from discord.ext import commands
from discord import Message, Embed

from managers.cache import Cache
from managers.help import StealHelp
from tools.Session import Session
from managers.context import StealContext
from tools.Config import Colors, Emojis
from discord.ext import commands
from tools.View import VerifyView

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()

class Steal(commands.Bot):
	def __init__(self):
		self.errors = Dict[str, commands.CommandError]
		self._uptime = time.time()
		self.session = Session()
		self.cache = Cache()
		self.startTime = time.time()

		super().__init__(
			command_prefix=[';', 'sudo ', 'await '],
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
				await self.load_extension(f"{dir}.{module[:-3]}")
				log.info(f'Loaded module: {module}')
			except commands.ExtensionFailed:
				log.warning(f'Extension failed to load: {module}')
				raise
			except Exception as e:
				log.error(f'Error loading module {module}: {e}')

	async def start_loops(self) -> None:
		snipe_delete.start(self)
		reminder_task.start(self)
		change_status.start(self)

	async def __chunk_guilds(self):
		for guild in self.guilds:
			await asyncio.sleep(2)
			await guild.chunk(cache=True)

	async def on_ready(self) -> None:
		log.info(f'Logged in as {self.user.name}#{self.user.discriminator} ({self.user.id})')
		log.info(f'Connected to {len(self.guilds)} guilds')
		log.info(f'Connected to {len(self.users)} users')

		asyncio.ensure_future(self.__chunk_guilds())

		await self.start_loops()

	async def setup_hook(self) -> None:
		await self.load_modules('cogs')
		await self.load_modules('events')

		from cogs.Tickets import TicketModPanel, TicketClose, TicketCreate

		self.add_view(TicketClose())
		self.add_view(TicketCreate())
		self.add_view(TicketModPanel())
		self.add_view(VerifyView())

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

	@property
	def lines(self) -> int:
		"""
		Return the code's amount of lines
		"""

		lines = 0
		for d in [x[0] for x in os.walk(".") if not ".git" in x[0]]:
			for file in os.listdir(d):
				if file.endswith(".py"):
					with open(f"{d}/{file}", "r+", encoding="utf8") as fp:
						fp = fp.read()
						lines += len(fp.splitlines())
	
		return lines

	def ordinal(self, number: int) -> str:
		"""
		convert a number to an ordinal number (ex: 1 -> 1st)
		"""

		return num2words(number, to="ordinal_num")

	async def getbyte(self, url: str) -> BytesIO:

		return BytesIO(await self.session.get_bytes(url))

		result = []
		for name, count in intervals:
			value = uptime_seconds // count
			if value:
				uptime_seconds -= value * count
				result.append(f"{int(value)} {name}{'s' if value > 1 else ''}")

		return ', '.join(result)
	"""
	async def dominant_color(self, url: Union[discord.Asset, str]) -> int:
		if isinstance(url, discord.Asset):
			url = url.url

		img = Image.open(BytesIO(await self.session.get_bytes(url)))
		img.thumbnail((32, 32))
		img=img.convert('RGBA')

		colors = await asyncio.to_thread(lambda: colorgram.extract(img, 1))
		return discord.Color.from_rgb(*list(colors[0].rgb)).value"""

	async def dominant_color_url(self, url: Union[discord.Asset, str]) -> int:
		if isinstance(url, discord.Asset):
			url = url.url

		img = Image.open(BytesIO(await self.session.get_bytes(url)))
		img = img.convert('RGBA')
		img = img.resize((150, 150))	

		ar = np.asarray(img)	
		mask = ar[:, :, 3] > 0
		ar = ar[mask]		
		ar = ar[:, : 3].astype(float)	
		#A lot of shit i dont understand
		codes, dist = scipy.cluster.vq.kmeans(ar, 5)		
		vecs, dist = scipy.cluster.vq.vq(ar, codes)
		counts, bins = np.histogram(vecs, len(codes))		
		index_max = np.argmax(counts)
		#something!!!
		peak = codes[index_max]
		colour = binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii')
		#convert hex colour to arr gee bee :3
		rgb = tuple(int(colour[i:i+2], 16) for i in (0, 2, 4))
		return discord.Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]).value
	

	async def dominant_color(self, value: bytes) -> int:

		img = Image.open(BytesIO(value))
		img = img.convert('RGBA')
		img = img.resize((150, 150))	

		ar = np.asarray(img)	
		mask = ar[:, :, 3] > 0
		ar = ar[mask]		
		ar = ar[:, : 3].astype(float)	
		#A lot of shit i dont understand
		codes, dist = scipy.cluster.vq.kmeans(ar, 5)		
		vecs, dist = scipy.cluster.vq.vq(ar, codes)
		counts, bins = np.histogram(vecs, len(codes))		
		index_max = np.argmax(counts)
		#something!!!
		peak = codes[index_max]
		colour = binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii')
		#convert hex colour to arr gee bee :3
		rgb = tuple(int(colour[i:i+2], 16) for i in (0, 2, 4))
		return discord.Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]).value

	def humanize_date(self, date: datetime.datetime) -> str:
		"""
		Humanize a datetime (ex: 2 days ago)
		"""

		if date.timestamp() < datetime.datetime.now().timestamp():
			return f"{(precisedelta(date, format='%0.0f').replace('and', ',')).split(', ')[0]} ago"
		else:
			return f"in {(precisedelta(date, format='%0.0f').replace('and', ',')).split(', ')[0]}"

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
