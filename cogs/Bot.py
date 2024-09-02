import base64
import os

import discord
import sys
import logging
import requests
from discord.ext import commands, tasks
import random
from dotenv import *
from discord import Color
import datetime
import time
import math
from discord.ext.commands import *
from tools.Config import Auth
from tools.View import UrlView
import asyncio
import psutil
import humanize
import asqlite

from tools.EmbedBuilder import EmbedBuilder, EmbedScript
from tools.EmbedBuilderUi import EmbedEditor, Embed

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis


class BotManagement(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = f"Manage {self.bot.user}."

	@group(
			name='profile',
			description='Manages Profile.'
	)
	async def profile(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.plshelp()
	@profile.command(
			name='pfp', 
			description='Changes bot pfp.', 
			aliases=['pic', 'avatar']
	)
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

	@profile.command(
			name='banner',
			description='Changes bot banner.', 
			aliases=['ban']
	)
	async def profilebanner(self, ctx: StealContext, image:Optional[discord.Attachment]) -> None:
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

	@profile.command(
			name='name', 
			description='Changes bot name.'
	)
	async def profilename(self, ctx: StealContext, username:str) -> None:
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

	@profile.command(
			name='fetchpfp',
			description='Fetches bot pfp.',
			alises=['getpfp']
	)
	async def fetchpfp(self, ctx: StealContext) -> None:
		if ctx.author.id in self.bot.owner_ids:
			if self.bot.user.display_avatar:
				await ctx.reply(
					embed=discord.Embed(
						title=f"{self.bot.user.name.split('#')[0]}'s pfp.",
						url=ctx.me.display_avatar.url,
						color=Colors.BASE_COLOR
					).set_image(url=ctx.me.display_avatar)
				)
			else:
				return await ctx.deny(f"{self.bot.user.name.split('#')[0]} does not have an avatar.")
		else:
			return await ctx.deny("Fuck off.")

	@profile.command(
			name='fetchbanner', 
			description='Fetches bot banner.', 
			alises=['getbanner']
	)
	async def fetchbanner(self, ctx: StealContext) -> None:
		if ctx.author.id in self.bot.owner_ids:
			user = await self.bot.fetch_user(ctx.me.id)
			if user.banner:
				await ctx.reply(
					embed=discord.Embed(
						title=f"{self.bot.user.name.split('#')[0]}'s banner.",
						url=user.banner.url,
						color=Colors.BASE_COLOR
					).set_image(url=user.banner)
				)
			else:
				return await ctx.deny(f"{self.bot.user.name.split('#')[0]} does not have a custom banner.")
		else:
			return await ctx.deny("Fuck off.")

	@command(
			name='bot',
			description='The invite for the bot.',
			aliases=['inv', 'steal']
	)
	async def invite(self, ctx: StealContext) -> None:
		view = UrlView(Auth.invite, "Steal")
		out = await ctx.send(content=ctx.author.mention, view=view)
		view.message = out 

	@command(
			name='reload'
	)
	async def reload(self, ctx: StealContext, cog) -> None:
		if ctx.author.id in self.bot.owner_ids:
			cog=cog + ".py"
			if cog in os.listdir("./cogs"):
					await ctx.bot.reload_extension(f"cogs.{cog[:-3]}")
					await ctx.message.add_reaction(
						Emojis.APPROVE
					)
			else:
				return await ctx.deny(f"`{cog}` is not a valid cog.")
		else:
			return await ctx.deny("Fuck off.")
	
	@command(
			name='load'
	)
	async def load(self, ctx: StealContext, cog) -> None:
		if ctx.author.id in self.bot.owner_ids:
			cog=cog + ".py"
			if cog.capitalize() in os.listdir("./cogs"):
					await ctx.bot.load_extension(f"cogs.{cog[:-3]}")
					await ctx.message.add_reaction(
						Emojis.APPROVE
					)
			else:
				return await ctx.deny(f'{cog} is not a valid cog.')
		else:
			return await ctx.deny("Fuck off.")
	
	@command(
			name='sync'
	)
	async def sync(self, ctx: StealContext) -> None:
		if ctx.author.id in self.bot.owner_ids:
			await self.bot.tree.sync()
			await ctx.message.add_reaction(
				Emojis.APPROVE
			)
		else:
			return await ctx.deny("Fuck off.")
	@Cog.listener()
	async def on_message(self, message: discord.Message) -> None:
		if isinstance(message.channel, discord.DMChannel):
			if message.author.id not in self.bot.owner_ids:
				return
		else:
			if message.author.bot:
				return
			if message.content == f"{self.bot.user.mention}":
				commands = [command for command in set(self.bot.walk_commands())] #if command.cog_name not in ['BotManagement', 'Auth', 'Profile', 'Bs

				embed = discord.Embed(
					color = Colors.BASE_COLOR,
					description=f"[**{self.bot.user.name.split("#")[0]}**]({Auth.invite}) info\n>>> **Commands:** `{len(commands)}`\n**Lines:**`{humanize.intcomma(self.bot.lines)}`\n**Guilds:**`{len(self.bot.guilds):,}`\n**Users:**`{len(self.bot.users):,}`\n**Command prefix:** `{self.bot.command_prefix[0]}`"
				)
				embed.add_field(
					name="Uptime",
					value=f"`{humanize.naturaldelta(datetime.timedelta(seconds=int(round(time.time()-self.bot.startTime))))}`"
				).set_author(
					name=message.author,
					icon_url=message.author.display_avatar.url
				)
				embed.set_thumbnail(url=self.bot.user.display_avatar.url)

				await message.reply(embed=embed)

			elif "steal" in message.content.lower() and not message.content.startswith(";"):
				return await message.reply("Love steal 😩")

	@group(
		name='system',
		aliases=['sys'],
		description='System commands.'
	)
	async def system(self, ctx: StealContext) -> None:
		if ctx.invoked_subcommand is None:
			return await ctx.plshelp()
	def restart_bot(self):
		os.execv(sys.executable, ["python3"] + sys.argv)

	@system.command(
			name='Restart', 
			aliases=['rs', 'reboot'], 
			description='Restarts the bot.'
	)
	async def systemrestart(self, ctx: StealContext) -> None:
		if ctx.author.id in self.bot.owner_ids:
			await ctx.approve(f"{self.bot.user} proccess is restarting.")
			await self.restart_bot()
		else: 
			return await ctx.deny("Fuck off.")

	@command(
			name="guilds",
			description='Guilds the bot is in.',
			aliases=["servers"]
	)
	@guild_only()
	async def guilds(self, ctx: StealContext) -> None:

		guilds = [guild for guild in self.bot.guilds]

		if not guilds:
			return await ctx.warn(f"The bot is in no guilds.")
			

		count = 0
		embeds = []
		
		entries = [
			f"`{i}` {b.name} (`{b.owner}`)"
			for i, b in enumerate(guilds, start=1)
		]

		l = 5

		embed = discord.Embed(
			color=Colors.BASE_COLOR,
			description="",
			title=f"Guilds (`{len(entries)}`)",
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
					description="",
					title=f"Guilds (`{len(entries)}`)",
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
			name="notice",
			description="Sends a notice to all bot guilds."
	)
	async def notice(self, ctx: StealContext, *, script:str) -> None:

		if not ctx.author.id in self.bot.owner_ids: return await ctx.deny("Fuck off.")

		count = 0	

		parsed = EmbedBuilder.embed_replacement(ctx.author, script)
		content, embed, view = await EmbedBuilder.to_object(parsed)

		for guild in self.bot.guilds:

			if guild.system_channel:

				try:
					await guild.system_channel.send(content=content, embed=embed, view=view)
					count += 1
				except:
					return
		
		await ctx.approve(f"Successfully notified {count} guilds with this script:")
		await ctx.send(content=content, embed=embed, view=view)

	@command(
			name='lsmsg'
	)
	async def lsmsg(self, ctx: StealContext):
		if ctx.author.id not in self.bot.owner_ids: return await ctx.deny("Fuck off.")
		await ctx.message.add_reaction("✅")
		mems = [i for i in ctx.guild.members]
		if not ctx.guild.chunked:
			await ctx.guild.chunk(cache=True)
		
		for i in ctx.guild.channels:
			if isinstance(i,discord.TextChannel):
				async for message in i.history(after=datetime.datetime.utcnow()-datetime.timedelta(days=60), limit=None):
					print(f"{i.name} ~~ {message.author.name} ~~ {message.content} || {message.created_at.day}/{message.created_at.month}/{message.created_at.year}")
					if isinstance(message.author, discord.Member) and message.author in mems:
						mems.remove(message.author)
						print(f"Name  :  {message.author.name}  ||  Id  :  {message.author.id}")
		
		with open("members.txt", "w+") as fp:
			for mem in mems:
				fp.write(f"NAME  :  {mem.name}  ||  ID  :  {mem.id}\n")
			fp.close()
		await ctx.message.add_reaction("🌟")



	async def file_send(self, ctx: StealContext, filename, user):
		user = await self.bot.fetch_user(user.id)
		files_to_upload=[filename]
		dm_channel = await user.create_dm()
		all_sent=False
		for file in files_to_upload:
			for root, _, filenames in os.walk("."):
				for f in filenames:
					if f.lower() == file.lower():
						filepath = os.path.join(root, f)
						await dm_channel.send(file=discord.File(fp=filepath))
						logging.info(f"{self.bot.user} sent {file} to {user}")
						all_sent = True
		if all_sent:
			return await ctx.reply(
						embed=discord.Embed(
							description=f"{Emojis.APPROVE} File **{filename.capitalize()}** sent successfully", color=Colors.APPROVE_COLOR
						).add_field(
							name="Task",
							value="File",
						).add_field(
							name="Status",
							value="Passed"
						).add_field(
							name="File",
							value=f"{filename.capitalize()}",
						).set_author(
							name=self.bot.user,
							icon_url=self.bot.user.display_avatar,
						),
				)
		else:
			return await ctx.reply(
				embed=discord.Embed(
					description=f"{Emojis.DENY} File **{filename.capitalize()}** not found!", color=Colors.DENY_COLOR
				).add_field(
					name="Task",
					value="Root",
				).add_field(
					name="Status",
					value="File"
				).add_field(
					name="File",
					value=f"{filename.capitalize()}",
				).set_author(
					name=self.bot.user,
					icon_url=self.bot.user.display_avatar,
				),
			)

	@command(
			name="root",
			description="sends a file"
	)
	async def backup_command(self, ctx: StealContext, filename: str):
		if ctx.author.id in self.bot.owner_ids:
			return await self.file_send(ctx, filename, ctx.author)
		return await ctx.deny("Fuck off.")

	@command()
	async def drop(self, ctx: StealContext, table: str):
		if not ctx.author.id in self.bot.owner_ids: return
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(f"DROP TABLE {table}")

				await ctx.approve("dropped")

	@command()
	async def trace(self, ctx: StealContext, *, code:str):
		if ctx.author.id in self.bot.owner_ids:
			async with asqlite.connect("main.db") as db:
				async with db.cursor() as cursor:
					await cursor.execute(
						"CREATE TABLE IF NOT EXISTS errors(code TEXT UNIQUE, guildid INTEGER, channelid INTEGER, userid INTEGER, time INTEGER, error TEXT, command TEXT)"
					)

					cur = await cursor.execute(
						"SELECT * FROM errors WHERE code = $1",
						code,
					)

					row = await cur.fetchone()

					if not row:
						return await ctx.warn("**Exception code** not found.")
					
					guild = self.bot.get_guild(row[1])
					channel = self.bot.get_channel(row[2])
					user = self.bot.get_user(row[3])
					time = discord.utils.format_dt(datetime.datetime.fromtimestamp(row[4]))
					command = row[6]
					error = row[5]

					try:
						await ctx.author.send(
							embed=discord.Embed(
								title=f"Exception traceback.",
								color=Colors.APPROVE_COLOR,
								description=f"> **Guild**: `{guild.name}`\n> **Channel**: `{channel.name}`\n> **User**: {user.mention} (`{user.name}`)\n> **Time**: {time}\n> **Command**: `{command}`",
							).set_thumbnail(
								url=guild.icon.url,
							).add_field(
								name="Exception",
								value=f"\n```bash\n{error}```"
							)
						)

						await ctx.message.add_reaction(
							Emojis.APPROVE
						)

					except:
						return await ctx.warn("**Failed** to send you the **Exception traceback**.")
		else:
			return await ctx.deny(f"Only owners of [**{self.bot.user.name.split("#")[0]}**]({Auth.invite}) can run this command.")

	@group(
			name="blacklist",
			description="Blacklists a user/guild from using the bot.",
	)
	async def blacklist(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return

	@blacklist.command(
			name="user",
			description="Blacklists a user",
	)
	async def userblacklist(self, ctx: StealContext, user: discord.User):
		if ctx.author.id not in self.bot.owner_ids: await ctx.deny("Fuck off.")
		if user.id in self.bot.owner_ids: await ctx.deny("Fuck off.")
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS userblacklist(userid INTEGER)"
				)

				cur = await cursor.execute(
					"SELECT * FROM userblacklist WHERE userid = $1",
					user.id,
				)

				row = await cur.fetchone()

				if not row:
					await cursor.execute(
						"INSERT INTO userblacklist (userid) VALUES ($1)",
						user.id,
					)

					try:
						await user.send(
							embed=discord.Embed(
								description=f"{Emojis.DENY} {user.mention}: You have been blacklisted from using {self.bot.user.name.split("#")[0]}",
								color=Colors.DENY_COLOR
							).set_author(
								name=self.bot.user,
								icon_url=self.bot.user.display_avatar.url
							)
						)
					except:
						pass

					return await ctx.approve(f"Blacklisted user **{user}**")
				
				return await ctx.warn(f"{user} is already blacklisted.")

	@group(
			name="unblacklist",
			description="Unblacklists a user/guild from using the bot."
	)
	async def unblacklist(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.plshelp()

	@unblacklist.command(
			name="user",
			description="Blacklists a user",
	)
	async def userunblacklist(self, ctx: StealContext, user: discord.User):
		if ctx.author.id not in self.bot.owner_ids: await ctx.deny("Fuck off.")
		if user.id in self.bot.owner_ids: await ctx.deny("Fuck off.")
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS userblacklist(userid INTEGER)"
				)

				cur = await cursor.execute(
					"SELECT * FROM userblacklist WHERE userid = $1",
					user.id,
				)

				row = await cur.fetchone()

				if row:
					await cursor.execute(
						"DELETE FROM userblacklist WHERE userid = $1",
						user.id,
					)

					return await ctx.approve(f"Unblacklisted user **{user}**")
				
				return await ctx.warn(f"{user} is not blacklisted.")


async def setup(bot):
	await bot.add_cog(BotManagement(bot))