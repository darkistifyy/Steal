import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import *
from discord import Color
from discord.ui import Button, View, button
from typing import Optional, Literal
import datetime
import asyncio

from tools.Steal import Steal
from managers.context import StealContext
from managers.interaction import PatchedInteraction

from typing import List, Optional
from tools.Config import Colors, Emojis, Guild

class DownloadAsset(discord.ui.View):
	def __init__(self, url: str):
		super().__init__(timeout=30)
		self.url = url
		self.add_item(discord.ui.Button(label='📁', style=discord.ButtonStyle.blurple, url=self.url))
	
	async def on_timeout(self):
		for child in self.children:
			child.disabled = True
		await self.message.edit(view=self)

class Invite(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=60)
		self.add_item(discord.ui.Button(label='Support server', emoji=f'{Emojis.INFO}', style=discord.ButtonStyle.blurple, url=Guild.INVITE))
	
	async def on_timeout(self):
		for child in self.children:
			child.disabled = True
		await self.message.edit(view=self)

class UrlView(discord.ui.View):
	def __init__(self, url, label:Optional[str] = "URL"):
		self.url = url
		self.label = label
		super().__init__(timeout=60)
		self.add_item(discord.ui.Button(label=label, emoji=f'{Emojis.INFO}', style=discord.ButtonStyle.blurple, url=self.url))
	
	async def on_timeout(self):
		for child in self.children:
			child.disabled = True
		await self.message.edit(view=self)