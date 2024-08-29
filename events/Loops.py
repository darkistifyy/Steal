from __future__ import annotations

import json
import random
import datetime
from datetime import datetime
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
				if datetime.now().timestamp() > result[3]:
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
