import base64
import os

import discord
import sys
import requests
from discord.ext import commands
from dotenv import *
from discord import Color
import datetime
import time
from discord.ext.commands import *
from tools.Config import Auth

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis


class BotManagement(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.startTime = time.time()

	@group(name='profile', description='Manages Profile.')
	async def profile(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `profile`.')
			return

	@profile.command(name='pfp', description='Changes bot pfp.', aliases=['pic', 'avatar'])
	async def profilepfp(self, ctx: StealContext, image:Optional[discord.Attachment] = None) -> None:
		if image is None:
			try:
				await self.bot.user.edit(avatar=None)
				await ctx.approve("Removed bot profile picture.")
			except Exception as e:
				return await ctx.deny(f"An error occurred: {e}", color=Color.red())	
		if ctx.author.id in self.bot.owner_ids:
			try:
				response = requests.get(image)
				response.raise_for_status()
				encoded_image = base64.b64encode(response.content).decode("utf-8")

				headers = {
					"Authorization": f"Bot {Auth.token}",
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
					"Content-Type": "application/json",
				}
				data = {"avatar": f"data:image/png;base64,{encoded_image}"}
				url = "https://discord.com/api/v9/users/@me"
				response = requests.patch(url, headers=headers, json=data)

				if response.status_code != 200:
					return await ctx.deny(f"An error occurred: {response.json()}")
					

				await ctx.approve("Updated bot profile picture.")

			except Exception as e:
				return await ctx.deny(f"An error occurred: {e}", color=Color.red())
		else:
			return await ctx.deny("Fuck off.")

	@profile.command(name='banner', description='Changes bot banner.', aliases=['ban'])
	async def profilebanner(self, ctx: StealContext, image:Optional[discord.Attachment]):
		if image is None:
			try:
				await self.bot.user.edit(avatar=None)
				await ctx.approve("Removed bot banner.")
			except Exception as e:
				return await ctx.deny(f"An error occurred: {e}", color=Color.red())	
		if ctx.author.id in self.bot.owner_ids:
			try:
				response = requests.get(image)
				response.raise_for_status()
				encoded_image = base64.b64encode(response.content).decode("utf-8")

				headers = {
					"Authorization": f"Bot {Auth.token}",
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
					"Content-Type": "application/json",
				}
				data = {"banner": f"data:image/png;base64,{encoded_image}"}
				url = "https://discord.com/api/v9/users/@me"
				response = requests.patch(url, headers=headers, json=data)

				if response.status_code != 200:
					return await ctx.deny(f"An error occurred: {response.json()}")
					

				await ctx.approve("Updated bot banner.")

			except Exception as e:
				return await ctx.deny(f"An error occurred: {e}", color=Color.red())
		else:
			return await ctx.deny("Fuck off.")

	@profile.command(name='name', description='Changes bot name.')
	async def profilename(self, ctx: StealContext, username:str):
		if ctx.author.id in self.bot.owner_ids:
			try:
				headers = {
					"Authorization": f"Bot {Auth.token}",
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
					"Content-Type": "application/json",
				}
				data = {"username": f"{username}"}
				url = "https://discord.com/api/v9/users/@me"
				response = requests.patch(url, headers=headers, json=data)

				if response.status_code != 200:
					return await ctx.deny(f"An error occurred: {response.json()}")
					

				await ctx.approve("Updated bot username.")

			except Exception as e:
				return await ctx.deny(f"An error occurred: {e}", color=Color.red())
		else:
			return await ctx.deny("Fuck off.")

	@profile.command(name='fetchpfp', description='Fetches bot pfp.', alises=['getpfp'])
	async def fetchpfp(self, ctx: StealContext) -> None:
		if ctx.author.id in self.bot.owner_ids:
			if self.bot.user.display_avatar:
				await ctx.reply(
					embed=discord.Embed(
						title=f"{self.bot.user.name.split("#")[0]}'s pfp.",
						url=ctx.me.display_avatar.url,
						color=Colors.BASE_COLOR
					).set_image(url=ctx.me.display_avatar)
				)
			else:
				return await ctx.deny(f"{self.bot.user.name.split("#")[0]} does not have an avatar.")
		else:
			return await ctx.deny("Fuck off.")

	@profile.command(name='fetchbanner', description='Fetches bot banner.', alises=['getbanner'])
	async def fetchbanner(self, ctx: StealContext) -> None:
		if ctx.author.id in self.bot.owner_ids:
			user = await self.bot.fetch_user(ctx.me.id)
			if user.banner:
				await ctx.reply(
					embed=discord.Embed(
						title=f"{self.bot.user.name.split("#")[0]}'s banner.",
						url=user.banner.url,
						color=Colors.BASE_COLOR
					).set_image(url=user.banner)
				)
			else:
				return await ctx.deny(f"{self.bot.user.name.split("#")[0]} does not have a custom banner.")
		else:
			return await ctx.deny("Fuck off.")

	@command(name='reload')
	async def reload(self, ctx: StealContext, cog):
		if ctx.author.id in self.bot.owner_ids:
			cog=cog + ".py"
			if cog in os.listdir("./cogs"):
					await ctx.bot.reload_extension(f"cogs.{cog[:-3]}")
					await ctx.message.add_reaction(
						"✅"
					)
			else:
				return await ctx.deny(f"`{cog}` is not a valid cog.")
		else:
			return await ctx.deny("Fuck off.")
	
	@command(name='load')
	async def load(self, ctx: StealContext, cog):
		if ctx.author.id in self.bot.owner_ids:
			cog=cog + ".py"
			if cog in os.listdir("./cogs"):
					await ctx.bot.load_extension(f"cogs.{cog[:-3]}")
					await ctx.message.add_reaction(
						"✅"
					)
			else:
				return await ctx.deny(f'{cog} is not a valid cog.')
		else:
			return await ctx.deny("Fuck off.")
	
	@command(name='sync')
	async def sync(self, ctx: StealContext):
		if ctx.author.id in self.bot.owner_ids:
			await self.bot.tree.sync()
			await ctx.message.add_reaction(
				"✅"
			)
		else:
			return await ctx.deny("Fuck off.")
	@Cog.listener()
	async def on_message(self, message: discord.Message) -> None:
		if message.author.bot:
			return
		if message.content == f"{self.bot.user.mention}":
			return await message.reply(embed=discord.Embed(description=f" Hi {message.author}. I am `{self.bot.user}` running on `Dpy Version {discord.__version__}`.\n Use `{self.bot.command_prefix[0]}help` to get started.", color=Colors.BASE_COLOR).add_field(
				   name="Prefix:",
			   	value=f"{self.bot.command_prefix[0]}"
			).add_field(
						 name="Uptime:",
						 value=f"{datetime.timedelta(seconds=int(round(time.time()-self.startTime)))}"
			).add_field(
				name=f'Owner:',
				value=f'<@{self.bot.owner_ids[0]}>'
			).set_author(
				name=f'{message.author}',
				icon_url=f'{message.author.display_avatar.url if message.author.display_avatar else None}'
			))

	@group(
		name='system',
		aliases=['sys'],
		description='System commands.'
	)
	async def system(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			await ctx.deny(f"{ctx.invoked_subcommand} is not a valid subcommand of `system`")
	def restart_bot(self):
		os.execv(sys.executable, ["python3"] + sys.argv)

	@system.command(name='Restart', aliases=['rs', 'reboot'], description='Restarts the bot.')
	async def systemrestart(self, ctx: StealContext):
		if ctx.author.id in self.bot.owner_ids:
			await ctx.approve(f"{self.bot.user} proccess is restarting.")
			await self.restart_bot()
		else: 
			return await ctx.deny("Fuck off.")

async def setup(bot):
	await bot.add_cog(BotManagement(bot))