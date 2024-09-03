from __future__ import annotations

import json
import random
import datetime
from typing import List, Literal, Optional

import aiohttp
from discord import Embed, NotFound, AllowedMentions

from discord.ext import tasks
from pydantic import BaseModel
from tools.Config import Emojis
import asqlite
import discord
from discord.ext.commands import Bot
from tools.Config import Emojis, Colors


from requests import HTTPError
import json

@tasks.loop(hours=2)
async def snipe_delete(bot: Bot):
	for m in ["snipe", "edit_snipe", "reaction_snipe"]:
		bot.cache.delete(m)

@tasks.loop(seconds=5)
async def reminder_task(bot: Bot):
	async with asqlite.connect("main.db") as db:
		async with db.cursor() as cursor:

			await cursor.execute(
				"CREATE TABLE IF NOT EXISTS reminder(guildid INTEGER, userid INTEGER, channelid INTEGER, time INTEGER, task TEXT)"
			)

			cur = await cursor.execute(
				"SELECT * FROM reminder"
			)

			results = await cur.fetchall()

			for result in results:
				if datetime.datetime.now().timestamp() > result[3]:
					channel = bot.get_channel(int(result[2]))
					if channel:
						if not channel.guild.chunked:
							await channel.guild.chunk(cache=True)

						member = channel.guild.get_member(result[1])
						if member:
							
							await channel.send(
								content=member.mention,
								embed=discord.Embed(
									description=f"> {Emojis.TIME} **Remember** to do your task, **{result[4]}**",
									color=Colors.BASE_COLOR
								)
							)
							await db.execute(
								"""
								DELETE FROM reminder 
								WHERE guildid = $1 
								AND userid = $2 
								AND channelid = $3
								""",
								channel.guild.id,
								member.id,
								channel.id,
							)

@tasks.loop(seconds=10)
async def change_status(bot: Bot):
	statuses = [
		discord.Activity(type=discord.ActivityType.listening, name=f"🎙️ ;help"),
	  	discord.Activity(type=discord.ActivityType.watching, name=f"🔗 .gg/fembakery"),
		discord.Activity(type=discord.ActivityType.watching, name="🟧⬛ that goodie"),
		discord.Activity(type=discord.ActivityType.playing, name="👅 with ur mum")
	]
	temp = None	
	if bot.activity:
		if bot.activity.name in [status.name for status in statuses]:
			temp = statuses.remove(bot.status)  
	if temp:
		status = random.choice(temp)
		temp = None		
	if not temp:
		status = random.choice(statuses)	
	await bot.change_presence(activity=status)

@tasks.loop(seconds=10)
async def giveaway_check(bot: Bot):
	async with asqlite.connect("main.db") as db:
		async with db.cursor() as cursor:

			await cursor.execute(
				"CREATE TABLE IF NOT EXISTS giveaways(guildid INTEGER, channelid INTEGER, messageid INTEGER, prize TEXT, time INTEGER, ended BOOLEAN NOT NULL CHECK (ended IN (0, 1)))"
			)

			cur = await cursor.execute(
				"SELECT * FROM giveaways"
			)

			rows = await cur.fetchall()

			if not rows:
				return

			for row in rows:
				try:
					time = row[4]
					ended = row [5]
					if datetime.datetime.now().timestamp() > time and int(ended) != 1:
						guild = bot.get_guild(row[0])
						channel = guild.get_channel(row[1])
						message = await channel.fetch_message(row[2])
						prize = row [3]
						
						entries = []

						for reaction in message.reactions:
							if reaction.emoji == Emojis.GIVEAWAY:
								async for user in reaction.users(limit=None):
									if user.id != guild.me.id and user in guild.members:
										entries.append(user.id)

						await cursor.execute(
							"UPDATE giveaways SET ended = $1",
							1.0,
						)

						await db.commit()

						if not entries:
							if "GIVEAWAY ENDED" in message.content: return
							embed = discord.Embed(
								title=f"{prize}",
								description=f"React below with {Emojis.GIVEAWAY} to enter the giveaway!\n> There were not enough **giveaway** entrants.",
								color=Colors.BASE_COLOR,
							)

							return await message.edit(content="GIVEAWAY ENDED.", embed=embed)

						roll = random.choice(entries)
						winner = guild.get_member(roll)

						if "GIVEAWAY ENDED" in message.content: return
						embed = discord.Embed(
							title=f"{prize}",
							description=f"React below with {Emojis.GIVEAWAY} to enter the giveaway!\n> Ended {discord.utils.format_dt(datetime.datetime.fromtimestamp(time), style="R")} 🎉",
							color=Colors.BASE_COLOR,
						)

						await message.edit(content="GIVEAWAY ENDED.", embed=embed)

						await message.reply(f"Congratulations, {winner.mention}, you won **{prize}**!")	
				except:
					await cursor.execute(
						"DELETE FROM giveaways WHERE guildid = $1 AND channelid = $2 AND messageid = $3",
						row[0], row[1], row[2],
					)

					await db.commit()


@tasks.loop(minutes=10)
async def giveaway_clear(bot: Bot):
	async with asqlite.connect("main.db") as db:
		async with db.cursor() as cursor:

			await cursor.execute(
				"CREATE TABLE IF NOT EXISTS giveaways(guildid INTEGER, channelid INTEGER, messageid INTEGER, prize TEXT, time INTEGER, ended BOOLEAN NOT NULL CHECK (ended IN (0, 1)))"
			)

			cur = await cursor.execute(
				"SELECT * FROM giveaways"
			)

			rows = await cur.fetchall()

			if not rows: 
				return

			for row in rows:
				if datetime.datetime.now().timestamp() > (datetime.datetime.fromtimestamp(row[4]) + datetime.timedelta(minutes=10)).timestamp():
					await cursor.execute(
						"DELETE FROM giveaways WHERE guildid = $1 AND channelid = $2 AND messageid = $3 AND time = $4",
						row[0], row[1], row[2], row[4]
					)
				
@tasks.loop(minutes=10)
async def error_clear(bot: Bot):
	async with asqlite.connect("main.db") as db:
		async with db.cursor() as cursor:

			await cursor.execute(
				"CREATE TABLE IF NOT EXISTS errors(code TEXT UNIQUE, guildid INTEGER, channelid INTEGER, userid INTEGER, time INTEGER, error TEXT, command TEXT)"
			)

			cur = await cursor.execute(
				"SELECT * FROM errors"
			)

			rows = await cur.fetchall()

			if not rows: 
				return

			for row in rows:
				if datetime.datetime.now().timestamp() > (datetime.datetime.fromtimestamp(row[4]) + datetime.timedelta(days=1)).timestamp():
					await cursor.execute(
						"DELETE FROM errors WHERE code = $1 AND time = $2",
						row[0], row[4],
					)