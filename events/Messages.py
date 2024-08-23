import discord
from discord.ext import commands
from dotenv import *
from discord.ext.commands import *
import asqlite
import humanize
import datetime

from tools.Config import Emojis, Colors
from tools.Steal import Steal

url_prefixes = "https://discord.com/invite/", "discord.gg/", ".gg/"

class Messages(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.afkstatus = False
		self.invitestatus = False
		
	@Cog.listener("on_message")
	async def filter_message_invite_event(self, message: discord.Message) -> None:
		if message.author.bot: return
		if message.is_system(): return
		if not message.author: return
		if isinstance(message.channel, discord.DMChannel): return
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS invitesautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)))
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM invitesautomod WHERE guildid = $1 
					""", message.guild.id
				)

				toggle = await cur.fetchone()
				await cur.close()

				if toggle:
					if toggle[0] == 1:
						for prefix in url_prefixes:
							if prefix in message.content:
								split1 = message.content.split(prefix)[1]
								code = split1.split(" ")[0]

								try:
									invite = await self.bot.fetch_invite(code)
								except:
									return

								if invite:
									if invite.guild.id != message.guild.id:
										await message.author.send(
											embed=discord.Embed(
												description=f"{Emojis.WARN} {message.author.mention}: Sending invites to other guilds is blacklisted in **{message.guild.name}**.",
												color=Colors.WARN_COLOR
											)
										)
										try:
											return await message.delete()
										except:
											return
	
	@Cog.listener("on_message")
	async def filter_message_blacklist_event(self, message: discord.Message):
		if message.author.bot: return
		if message.is_system(): return
		if not message.author: return
		if isinstance(message.channel, discord.DMChannel): return
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM wordsautomod WHERE guildid = $1 
					""", message.guild.id
				)

				row = await cur.fetchone()

				if row:
					if row[1] == 1:

						if message.content.startswith(f"{self.bot.command_prefix[0]}filter words remove") or message.content.startswith(f"{self.bot.command_prefix[0]}filter words add"):
							if message.author.guild_permissions.manage_messages:
								return

						words = row[2]
						await cur.close()

						things = [word for word in words[0].split(",") if word]

						for thing in things:
							if thing.lower() in message.content.lower():
								await message.author.send(
									embed=discord.Embed(
										description=f"{Emojis.WARN} {message.author.mention}: The word **{thing}** is blacklisted in **{message.guild.name}**.",
										color=Colors.WARN_COLOR
									)
								)

								await message.delete()

	@Cog.listener("on_message")
	async def afk_message_event(self, message: discord.Message) -> None:
		if message.author.bot: return
		if message.is_system(): return
		if not message.author: return
		if isinstance(message.channel, discord.DMChannel): return
		if message.content.startswith(f"{self.bot.command_prefix[0]}afk"): return
		if self.afkstatus == message.author: return
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS afk(guildid INTEGER, userid, status, time)"
				)

				cur = await cursor.execute(
					"SELECT * FROM afk WHERE guildid = $1 AND userid = $2",
					message.guild.id, message.author.id,
				)

				row = await cur.fetchone()

				if row:
					self.afkstatus = True
					await cursor.execute(
						"DELETE FROM afk WHERE guildid = $1 AND userid = $2",
						message.guild.id, row[1],
					)

					await message.reply(
						embed=discord.Embed(
							description=f"Welcome back {message.author.mention}! You were gone for **{humanize.precisedelta(datetime.datetime.fromtimestamp(int(row[3])), format=f'%0.0f')}**",
							color=Colors.BASE_COLOR
						)
					)
				self.afkstatus = False

	@Cog.listener("on_message")
	async def afk_user_mention_event(self, message: discord.Message) -> None:
		if message.author.bot: return
		if message.is_system(): return
		if not message.author: return
		if isinstance(message.channel, discord.DMChannel): return
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS afk(guildid INTEGER, userid INTEGER, status TEXT, time INTEGER)"
				)

				cur = await cursor.execute(
					"SELECT * FROM afk WHERE guildid = $1 AND userid = $2",
					message.guild.id, message.author.id,
				)

				row = await cur.fetchall()

				if row:
					row = row[0]
					if row[1]:
						user = self.bot.get_user(row[1])
						if user.mentioned_in(message):
							status = row[2]
							await message.reply(
								embed=discord.Embed(
									description=f"{user.mention} is AFK with the status - **{status if status else "Unretriveable status"}**",
									color=Colors.BASE_COLOR
								)
							)
							
	@Cog.listener("on_message_delete")
	async def delete_snipe(self, message: discord.Message):
		if message.author.bot:
			return

		get_snipes = self.bot.cache.get("snipe")
		payload = [
			{
				"channel": message.channel.id,
				"name": str(message.author),
				"avatar": message.author.display_avatar.url,
				"message": message.content,
				"attachments": message.attachments,
				"stickers": message.stickers,
				"created_at": message.created_at.timestamp(),
			}
		]

		if get_snipes:
			temp = self.bot.cache.get("snipe")
			temp.append(
				{
					"channel": message.channel.id,
					"name": str(message.author),
					"avatar": message.author.display_avatar.url,
					"message": message.content,
					"attachments": message.attachments,
					"stickers": message.stickers,
					"created_at": message.created_at.timestamp(),
				}
			)
			return await self.bot.cache.set("snipe", temp)
		else:
			await self.bot.cache.set("snipe", payload)


	@Cog.listener("on_message_edit")
	async def edit_snipe(self, before: discord.Message, after: discord.Message):
		if before.author.bot:
			return
		if before.content == after.content:
			return

		get_snipes = self.bot.cache.get("edit_snipe")
		if get_snipes:
			temp = self.bot.cache.get("edit_snipe")
			temp.append(
				{
					"channel": before.channel.id,
					"name": str(before.author),
					"avatar": before.author.display_avatar.url,
					"before": before.content,
					"after": after.content,
					"edited_at": after.created_at.timestamp(),
				}
			)
			return await self.bot.cache.set("edit_snipe", temp)
		else:
			payload = [
				{
					"channel": before.channel.id,
					"name": str(before.author),
					"avatar": before.author.display_avatar.url,
					"before": before.content,
					"after": after.content,
					"edited_at": after.created_at.timestamp()
				}
			]
			return await self.bot.cache.set("edit_snipe", payload)

async def setup(bot):
	await bot.add_cog(Messages(bot))