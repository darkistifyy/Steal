from __future__ import annotations

from tools.Config import *
import discord
from discord.ext import *
from discord.ext.commands import *
import asqlite

from tools.Steal import Steal

bot = Steal()

@bot.event
async def on_message(message: discord.Message):
	async with asqlite.connect("main.db") as db:
		async with db.cursor() as cursor:
			await cursor.execute(
				"CREATE TABLE IF NOT EXISTS userblacklist(userid INTEGER)"
			)
			cur = await cursor.execute(
				"SELECT * FROM userblacklist WHERE userid = $1",
				message.author.id,
			)
			row = await cur.fetchone()
			if not row:
				return await bot.process_commands(message)

if __name__ == "__main__":
	bot.run(Auth.token)
