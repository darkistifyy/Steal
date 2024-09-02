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
import random

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
			brief="welcome",
			extras= {"permissions": ["manage_channels"]},
	)
	async def welcome(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.plshelp()
	

	@welcome.command(
			name="channel",
			description="The channel to send welcome messages to.",
			brief="welcome channel #welcomes",
			extras= {"permissions": ["manage_channels"]},
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

					return await ctx.approve(f"> {Emojis.APPROVE} {ctx.author.mention}: Set the **welcome** channel to {channel.mention} with the script \n```ruby\n{script}```")
						
				
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
			brief="welcome disable",
			extras= {"permissions": ["manage_channels"]},
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
			brief="welcome enable",
			extras= {"permissions": ["manage_channels"]},
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
			aliases=["code", "message"],
			brief="welcome script {content:sup {user.mention}}",
			extras= {"permissions": ["manage_channels"]},
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
			brief="welcome config",
			extras= {"permissions": ["manage_channels"]},
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
						description=f">>> **Channel**: {channel}\n**Toggle**: `{toggle.capitalize()}`",
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
			description="Test the boost response module",
			aliases=["send"],
			brief="welcome test",
			extras= {"permissions": ["manage_channels"]},
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
			brief="welcome clear",
			extras= {"permissions": ["manage_channels"]},
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
			brief="boost",
			extras= {"permissions": ["manage_channels"]},
	)
	async def boost(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.plshelp()
	

	@boost.command(
			name="channel",
			description="The channel to send boost response messages to.",
			brief="boost channel #boosts",
			extras= {"permissions": ["manage_channels"]},
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
							description=f"{Emojis.APPROVE} {ctx.author.mention}: Set **boost response** channel to {channel.mention} with the **script**\n```ruby\n{script}```",
							color=Colors.APPROVE_COLOR
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
			brief="boost disable",
			extras= {"permissions": ["manage_channels"]},
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
			brief="boost enable",
			extras= {"permissions": ["manage_channels"]},
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
			aliases=["code", "message"],
			brief="boost script {content:ty for the boost {user.mention}}",
			extras= {"permissions": ["manage_channels"]},
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
			description="Test the boost response module",
			aliases=["send"],
			brief="boost test",
			extras= {"permissions": ["manage_channels"]},
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
			brief="boost config",
			extras= {"permissions": ["manage_channels"]},
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
			brief="boost clear",
			extras= {"permissions": ["manage_channels"]},
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
			brief="logs",
			aliases=["log"],
			extras= {"permissions": ["manage_channels"]},
	)
	async def logs(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			await ctx.plshelp()
	
	@logs.command(
			name="messages",
			description="Log message events to a channel.",
			aliases=["msgs"],
			brief="logs messages #logs",
			extras= {"permissions": ["manage_channels"]},
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

	@group(
		name="giveaway",
		description="Giveaways.",
		aliases=["gw"],
		brief="giveaway",
		extras={"permissions" : ["manage_messages"]}

	)
	async def giveaway(self, ctx:StealContext):
		if not ctx.invoked_subcommand:
			await ctx.plshelp()
	
	@giveaway.command(
		name="create",
		description="Create a giveaway.",
		aliases=["start"],
		brief="giveaway create 1h #general custom role",
		extras={"permissions" : ["manage_messages"]}
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	async def giveaway_create(self, ctx: StealContext, duration: ValidTime, *, prize:str, channel: Optional[discord.abc.GuildChannel] = None):

		if not channel:
			channel = ctx.channel

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS giveaways(guildid INTEGER, channelid INTEGER, messageid INTEGER, prize TEXT, time INTEGER, ended BOOLEAN NOT NULL CHECK (ended IN (0, 1)))"
				)

				ends_in = datetime.datetime.now() + datetime.timedelta(seconds=duration)
				ends_in_timestamp = discord.utils.format_dt(ends_in, style="R")

				embed = discord.Embed(
					title=f"{prize}",
					description=f"React below with {Emojis.GIVEAWAY} to enter the giveaway!\n> Ends in {ends_in_timestamp}",
					color=Colors.BASE_COLOR,
				)

				embed.set_author(
					name=f"Giveaway by {ctx.author}",
					icon_url=ctx.author.display_avatar.url
				)

				out = await ctx.send(embed=embed)

				await out.add_reaction(
					Emojis.GIVEAWAY
				)

				await db.execute(
					"INSERT INTO giveaways(guildid, channelid, messageid, prize, time, ended) VALUES($1,$2,$3,$4,$5,$6)",
					ctx.guild.id, channel.id, out.id, prize, ends_in.timestamp(), 0
				)

				await db.commit()

	@giveaway.command(
		name="reroll",
		description="Re-Rolls a giveaway.",
		aliases=["rr", "redo"],
		brief="giveaway reroll [replytomessage]",
		extras={"permissions" : ["manage_messages"]}
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	async def giveaway_reroll(self, ctx: StealContext, message: Optional[discord.Message]):
		if not message:
			if not ctx.message.reference:
				return await ctx.warn("**Invalid Input Given**: `message is a required argument that is missing.`")
			messageid = ctx.message.reference.message_id
			try:
				message = await ctx.channel.fetch_message(messageid)
			except:
				return await ctx.deny("That message doesn't exist somehow 😭")

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS giveaways(guildid INTEGER, channelid INTEGER, messageid INTEGER, prize TEXT, time INTEGER, ended BOOLEAN NOT NULL CHECK (ended IN (0, 1)))"
				)

				cur = await cursor.execute(
					"SELECT * FROM giveaways WHERE guildid = $1 AND channelid = $2 AND messageid = $3",
					message.guild.id, message.channel.id, message.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("**Giveaway** not found or re-roll period expired.")
				
				if not row[5] or row[4] > datetime.datetime.now().timestamp():
					return await ctx.warn("That **giveaway** is still in progress.")
				
				entries = []

				for reaction in message.reactions:
					if reaction.emoji == Emojis.GIVEAWAY:
						async for user in reaction.users(limit=None):
							if user.id != message.guild.me.id:
								entries.append(user.id)
				
				if not entries:
					return await ctx.warn("There are no **giveaway** entrants.")

				roll = random.choice(entries)
				winner = message.guild.get_member(roll)

				await ctx.message.reply(f"The new winner is {winner.mention}, congrats for winning **{row[3]}**!")	

	@giveaway.command(
		name="end",
		description="Ends a giveaway.",
		brief="giveaway end [replytomessage]",
		aliases=["stop", "finish"],
		extras={"permissions" : ["manage_messages"]}
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	async def giveaway_end(self, ctx: StealContext, message: Optional[discord.Message]):
		if not message:
			if not ctx.message.reference:
				return await ctx.warn("**Invalid Input Given**: `message is a required argument that is missing.`")
			messageid = ctx.message.reference.message_id
			try:
				message = await ctx.channel.fetch_message(messageid)
			except:
				return await ctx.deny("That message doesn't exist somehow 😭")

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS giveaways(guildid INTEGER, channelid INTEGER, messageid INTEGER, prize TEXT, time INTEGER, ended BOOLEAN NOT NULL CHECK (ended IN (0, 1)))"
				)

				cur = await cursor.execute(
					"SELECT * FROM giveaways WHERE guildid = $1 AND channelid = $2 AND messageid = $3",
					message.guild.id, message.channel.id, message.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("**Giveaway** not found or re-roll period expired.")
				
				entries = []

				for reaction in message.reactions:
					if reaction.emoji == Emojis.GIVEAWAY:
						async for user in reaction.users(limit=None):
							if user.id != message.guild.me.id:
								entries.append(user.id)

				await cursor.execute(
					"UPDATE giveaways SET ended = $1, time = $2 WHERE guildid = $3 AND channelid = $4 AND messageid = $5",
					1.0, datetime.datetime.now().timestamp(), message.guild.id, message.channel.id, message.id,
				)

				await db.commit()
				if not entries:
					embed = discord.Embed(
						title=f"{row[3]}",
						description=f"React below with {Emojis.GIVEAWAY} to enter the giveaway!\n> There were not enough **giveaway** entrants.",
						color=Colors.BASE_COLOR,
					)
					return await message.edit(content="GIVEAWAY ENDED.", embed=embed)

				roll = random.choice(entries)
				winner = message.guild.get_member(roll)

				roll = random.choice(entries)
				winner = message.guild.get_member(roll)
				embed = discord.Embed(
					title=f"{row[3]}",
					description=f"React below with {Emojis.GIVEAWAY} to enter the giveaway!\n> Ended {discord.utils.format_dt(datetime.datetime.now(), style="R")} 🎉",
					color=Colors.BASE_COLOR,
				)

				await message.edit(content="GIVEAWAY ENDED.", embed=embed)
			
				return await message.reply(f"Congratulations, {winner.mention}, you won **{row[3]}**!")		

async def setup(bot):
	await bot.add_cog(Server(bot))
