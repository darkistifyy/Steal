from __future__ import print_function, annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import asyncio
import asqlite
from discord.ui import *
import humanize.number
import humanize.time
from sklearn import *
from tools.Steal import Steal
from managers.context import StealContext
from tools.Validators import ValidTime
from tools.EmbedBuilder import EmbedBuilder
import humanize
import datetime

from typing import List, Optional, Union
from tools.Config import Colors, Emojis

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from typing import Generator, Union, Optional

import discord
from discord.ext import commands

from managers.context import StealContext


class Server(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = "Manage guild shit"
		

	@group(
			name = "welcome",
			description="The welcoming members module.",
	)
	async def welcome(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `welcome`.')
	

	@welcome.command(
			name="channel",
			description="The channel to send welcome messages to.",
			aliases=["join"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomechannel(self, ctx: StealContext, channel:discord.TextChannel = None):
		if not channel: channel = ctx.channel

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					script = "{content:sup {user.mention}}"
					await cursor.execute(
						"INSERT INTO welcome (guildid, channelid, toggle, script) VALUES ($1, $2, $3, $4)",
						ctx.guild.id, channel.id, 1.0, script,
					)

					await db.commit()

					return await ctx.reply(
						embed=discord.Embed(
							description=f"> {Emojis.APPROVE} {ctx.author.mention}: Set the **welcome** channel to {channel.mention} with the script \n```ruby\n{script}```",
							color=Colors.APPROVE_COLOR
						)
					)
				
				toggle = row[2]

				if toggle != 1:
					return await ctx.warn("The **welcome** module is **disabled**.")

				await cursor.execute(
					"UPDATE welcome SET channelid = $1 WHERE guildid = $2",
					channel.id, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve(f"Set the **welcome** channel to {channel.mention}.")

	@welcome.command(
			name="disable",
			description="Disables the welcome module",
			aliases=["off"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomedisable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				toggle = row[2]

				if toggle != 1:
					return await ctx.warn("The **welcome** module is already **disabled**")
				
				await cursor.execute(
					"UPDATE welcome SET toggle = $1 WHERE guildid = $2",
					0, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve("**Disabled** the **welcome** module.")

	@welcome.command(
			name="enable",
			description="Enables the welcome module",
			aliases=["on"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomeenable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				toggle = row[2]

				if toggle != 0:
					return await ctx.warn("The **welcome** module is already **enabled**")
				
				await cursor.execute(
					"UPDATE welcome SET toggle = $1 WHERE guildid = $2",
					1, ctx.guild.id, 
				)
				
				await db.commit()

				await ctx.approve("**Enabled** the **welcome** module.")

	@welcome.command(
			name="script",
			description="The script for the welcome message.",
			aliases=["code", "message"]
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomescript(self, ctx: StealContext, *, script: Optional[str] = None):
		if not script:
			default = "{content:sup {user.mention}}"

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("The **welcome** channel has not been configured for this guild.")
				
				if str(row[3]) == str(script if script else default):
					return await ctx.warn("That is the same **script** as before, not updating.")
				
				await cursor.execute(
					"UPDATE welcome SET script = $1",
					script if script else default,
				)

				await db.commit()

				await ctx.approve(f"Set **channel** module script to {'default' if not script else ''} ```ruby\n{script if script else default}```")

	@welcome.command(
			name="config",
			description="The config for the welcome module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomeconfig(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				channelid = row[1]
				channel = self.bot.get_channel(channelid)

				if channel:
					channel = channel.mention
				else:
					channel = "Invalid channel."

				toggle_converter = {
					1 : "enabled",
					0 : "disabled",
				}

				toggle = toggle_converter.get(row[2], "❓")

				script = row[3]

				await ctx.reply(
					embed=discord.Embed(
						title="Welcome config",
						color=Colors.BASE_COLOR,
						description=f">>> **Channel**: `{channel}`\n**Toggle**: `{toggle.capitalize()}`",
					).add_field(
						name="Script",
						value=f"```ruby\n{script}```",
						inline=False
					).set_author(
						name=ctx.guild.name,
						icon_url=ctx.guild.icon.url if ctx.guild.icon else None
					)
				)

	@welcome.command(
			name="test",
			description="Test the boost response module"
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcometest(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				channel = self.bot.get_channel(row[1])

				if not channel:
					return await ctx.warn("The **welcome** channel is invalid!")
				
				parsed = EmbedBuilder.embed_replacement(ctx.author, row[3])
				content, embed, view = await EmbedBuilder.to_object(parsed)
				
				await channel.send(content=content, embed=embed, view=None)	

	@welcome.command(
			name="clear",
			description="Clears the welcome module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomeclear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				await cursor.execute(
					"DELETE FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				await db.commit()

				await ctx.approve("Cleared **welcome** module config.")

	@group(
			name = "boost",
			description="The boost response module.",
	)
	async def boost(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `boost`.')
	

	@boost.command(
			name="channel",
			description="The channel to send boost response messages to.",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostchannel(self, ctx: StealContext, channel:discord.TextChannel = None):
		if not channel: channel = ctx.channel

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					script = "{content:thanks for the boost {user.mention}}"
					await cursor.execute(
						"INSERT INTO boostresponse (guildid, channelid, toggle, script) VALUES ($1, $2, $3, $4)",
						ctx.guild.id, channel.id, 1.0, script,
					)

					await db.commit()

					return await ctx.reply(
						embed=discord.Embed(
							description=f"{Emojis.APPROVE} {ctx.author.mention}: Set **boost response** channel to {channel.mention} with the **script** ```{script}```",
							color=Colors.APPROVE_COLOR
						).set_footer(
							text=f"Use '{self.bot.command_prefix[0]}boost script <script>' to update the script.",
							icon_url=self.bot.user.display_avatar.url
						)
					)

				await cursor.execute(
					"UPDATE boostresponse SET channelid = $1 WHERE guildid = $2",
					channel.id, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve(f"Set **boost response** channel to {channel.mention}.")

	@boost.command(
			name="disable",
			description="Disables the boost response module",
			aliases=["off"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostdisable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				toggle = row[2]

				if toggle != 1:
					return await ctx.warn("The **boost response** module is already **disabled**")
				
				await cursor.execute(
					"UPDATE boostresponse SET toggle = $1 WHERE guildid = $2",
					0, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve("**Disabled** the **boost response** module.")

	@boost.command(
			name="enable",
			description="Enables the boost response module",
			aliases=["on"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostenable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				toggle = row[2]

				if toggle != 0:
					return await ctx.warn("The **boost response** module is already **enabled**")
				
				await cursor.execute(
					"UPDATE boostresponse SET toggle = $1 WHERE guildid = $2",
					1, ctx.guild.id, 
				)
				
				await db.commit()

				await ctx.approve("**Enabled** the **boost response** module.")

	@boost.command(
			name="script",
			description="The script for the boost response message.",
			aliases=["code", "message"]
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostscript(self, ctx: StealContext, *, script: Optional[str]):
		if not script: default = "{content:thanks for the boost {user.mention}}"

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("The **boost response** channel has not been configured for this guild.")
				
				if str(row[3]) == str(script if script else default):
					return await ctx.warn("That is the same script as before, not updating.")
				
				await cursor.execute(
					"UPDATE boostresponse SET script = $1",
					script if script else default,
				)

				await db.commit()

				await ctx.approve(f"Set **boost response** module script to {'default' if not script else ''} \n```ruby\n{default if not script else script}```")

	@boost.command(
			name="test",
			description="Test the boost response module"
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boosttest(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				channel = self.bot.get_channel(row[1])

				if not channel:
					return await ctx.warn("The **boost response** channel is invalid!")
				
				parsed = EmbedBuilder.embed_replacement(ctx.author, row[3])
				content, embed, view = await EmbedBuilder.to_object(parsed)
				
				await channel.send(content=content, embed=embed, view=None)	

	@boost.command(
			name="config",
			description="The config for the boost response module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostconfig(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				channelid = row[1]
				try:
					channel = self.bot.get_channel(channelid)
					channel = channel.mention
				except:
					channel = "Invalid channel"

				toggle_converter = {
					1 : "enabled",
					0 : "disabled",
				}

				toggle = toggle_converter.get(row[2], "❓")

				script = row[3]

				await ctx.reply(
					embed=discord.Embed(
						title="Boost response config",
						color=Colors.BASE_COLOR,
						description=f">>> **Channel**: `{channel}`\n**Toggle**: `{toggle.capitalize()}`"
					).add_field(
						name="Script",
						value=f"```ruby\n{script}```",
					).set_author(
						name=ctx.guild.name,
						icon_url=ctx.guild.icon.url if ctx.guild.icon else None
					)
				)

	@boost.command(
			name="clear",
			description="Clears the boost response module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostclear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				await cursor.execute(
					"DELETE FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				await db.commit()

				await ctx.approve("Cleared **boost response** module config.")

	@group(
			name="logs",
			description="Manage server logs n shit.",
	)
	async def logs(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `boost`.')
	
	@logs.command(
			name="messages",
			description="Log message events to a channel.",
			aliases=["msgs"]
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def messageslogs(self, ctx: StealContext, channel: Optional[discord.abc.GuildChannel] = None):
		if not channel: channel == ctx.channel
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS msglogs(guildid INTEGER UNIQUE, channelid INTEGER)"
				)

				await cursor.execute(
					"REPLACE INTO msglogs(guildid, channelid) VALUES($1, $2)",
					ctx.guild.id, channel.id,
				)
	
				await ctx.approve(f"Set **message logs** channel to {channel.mention}")

async def setup(bot):
	await bot.add_cog(Server(bot))
