import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import *
from discord import Color
from discord.ui import Button, View, button
from typing import Optional, Literal
import datetime
import asyncio
import humanize
import asqlite

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

class CustomView(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=60)
	
	async def on_timeout(self):
		for child in self.children:
			child.disabled = True
		await self.message.edit(view=self)


class MarryView(View):
	def __init__(self, ctx: Context, member: discord.User):
		super().__init__()
		self.ctx = ctx
		self.member = member
		self.status = False
		self.wedding = "💒"
		self.marry_color = 0xFF819F

	async def interaction_check(self, interaction: PatchedInteraction):
		if interaction.user == self.ctx.author:
			await interaction.warn(
				"You cannot interact with your own marriage",
			)
			return False
		elif interaction.user != self.member:
			await interaction.warn(
				"You are **not** involved in this embed",
			)
			return False
		return True

	@button(label="Marry", style=discord.ButtonStyle.success, custom_id="acceptmarriage")
	async def accept(self, interaction: PatchedInteraction, button: Button):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:
				cur = await cursor.execute(
					"SELECT * FROM marry WHERE $1 IN (author, soulmate)", self.ctx.author.id
				)
				data = await cur.fetchone()
				if data:
					return await interaction.warn(
						f"{self.ctx.author.mention} is **already** married",
					)

				cur = await cur.execute(
					"SELECT * FROM marry WHERE $1 IN (author, soulmate)", interaction.user.id
				)
				data = await cur.fetchone()
				if data:
					return await interaction.warn(
						"You are **already** married.",
					)

				await conn.execute(
					"INSERT INTO marry VALUES ($1,$2,$3)",
					self.ctx.author.id,
					self.member.id,
					datetime.datetime.now().timestamp(),
				)
				await conn.commit()
				embe = discord.Embed(
					color=Colors.BASE_COLOR,
					description=f"{self.wedding} {self.ctx.author.mention} You have married {self.member.mention}",
				)
				for child in self.children:
					child.disabled = True
				await interaction.response.edit_message(content=None, embed=embe, view=self)
				self.status = True

	@button(label="Decline", style=discord.ButtonStyle.danger, custom_id="declinemarriage")
	async def decline(self, interaction: PatchedInteraction, button: Button):
		embe = discord.Embed(
			color=Colors.BASE_COLOR,
			description=f"{self.ctx.author.mention} I'm sorry, but {self.member.mention} said no.",
		)
		for child in self.children:
			child.disabled = True
		await interaction.response.edit_message(content=None, embed=embe, view=self)
		self.status = True

	async def on_timeout(self):
		if self.status == False:
			embed = discord.Embed(
				color=0xFF819F,
				description=f"{self.member.mention} didn't reply in time :(",
			)
			try:
				for child in self.children:
					child.disabled = True
				await self.message.edit(content=None, embed=embed, view=self)
			except:
				pass



class DivorceView(discord.ui.View):
	def __init__(self, ctx: StealContext, member: discord.User, time):
		super().__init__()
		self.ctx = ctx
		self.member = member
		self.time = time

	async def interaction_check(self, interaction: PatchedInteraction):
		if interaction.user != self.ctx.message.author:
			await interaction.warn(
				"You are **not** involved in this embed",
			)
			return False
		return True

	@button(label="Divorce", style=discord.ButtonStyle.success, custom_id="acceptdivorce")
	async def divorceaccept(self, interaction: PatchedInteraction, button: Button):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:
				member = self.member
				await conn.execute(
					"DELETE FROM marry WHERE $1 IN (author, soulmate)", interaction.user.id
				)
				await conn.commit()
				await cursor.close()
				embe = discord.Embed(
					color=Colors.BASE_COLOR,
					description=f"**{interaction.user.mention}** divorced their partner, {member.mention}",
				)
				
				try:
					await member.send(
						f"💔 It seems like your partner **{interaction.user}** decided to divorce :(. Your relationship with them lasted **{humanize.precisedelta(datetime.datetime.fromtimestamp(int(self.time)), format=f'%0.0f')}**"
					)
				except:
					pass
			
				for child in self.children:
					child.disabled = True

				await interaction.response.edit_message(content=None, embed=embe, view=self)

	@button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="canceldivorce")
	async def divorcecancel(self, interaction: PatchedInteraction, button: Button):
		embe = discord.Embed(
			color=Colors.DENY_COLOR,
			description=f"**{interaction.user.mention}**: You changed your mind",
		)
		for child in self.children:
			child.disabled = True
		await interaction.response.edit_message(content=None, embed=embe, view=self)
		