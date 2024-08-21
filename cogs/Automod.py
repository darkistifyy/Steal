from __future__ import annotations

import discord
from discord.ext import commands
from discord.ext.commands import *
from typing import Optional, Union
import humanfriendly
import datetime
import asqlite
import math

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis



class Automod(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot


	@group(
			name="filter",
			description="Filter module."
	)
	async def filter(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `filter`.')
		
	
	@filter.group(
			name="invites",
			description="The invites filter module."
	)
	async def invites(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `invites`.')
		
	@invites.command(
			name="enable",
			description="Enables the invites filter module.",
			aliases=["on"]
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def invitesenable(self, ctx: StealContext):
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
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					await cursor.execute(
						"""
						INSERT INTO invitesautomod (guildid, toggle) VALUES ($1, $2)
						""", ctx.guild.id, 1.0, 
					)

					await conn.commit()

					return await ctx.approve("Enabled the **invites** automod module")

				if res[0] == 1:
					return await ctx.warn("The **invites** automod module is already **enabled**.")

				await cursor.execute(
					"""
					UPDATE invitesautomod SET toggle = $1 WHERE guildid = $2
					""", 1.0, ctx.guild.id, 
				)

				await conn.commit()

				return await ctx.approve("Enabled the **invites** filter module")

	@invites.command(
			name="disable",
			description="Disables the invites filter module.",
			aliases=["off"]
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def invitesdisable(self, ctx: StealContext):
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
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					return await ctx.warn("The **invites** filter module is not configured in this guild.")

				if res[0] == 0:
					return await ctx.warn("The **invites** filter module is already **disabled**.")

				await cursor.execute(
					"""
					UPDATE invitesautomod SET toggle = $1 WHERE guildid = $2
					""", 0, ctx.guild.id, 
				)

				await conn.commit()

				return await ctx.approve("Disabled the **invites** filter module")


	@invites.command(
			name="config",
			description="Sends the invites filter module config.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def invitesdconfig(self, ctx: StealContext):
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
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					return await ctx.warn("The **invites** filter module is not configured in this guild.")

				toggle_converter = {
					1 : "enabled",
					0 : "disabled",
				}

				toggle = toggle_converter.get(res[0], "❓")

				await ctx.neutral(f"{ctx.author.mention}: The **invites** filter module is **{toggle}**")

	@invites.command(
			name="clear",
			description="Clears the invites filter module config.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def invitesclear(self, ctx: StealContext):
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
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					return await ctx.warn("The **invites** filter module is not configured in this guild.")

				await cur.execute(
					"""
					DELETE FROM invitesautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)
				
				await conn.commit()

				return await ctx.approve(f"Cleared the **invites** filter module.")
			


	
	@filter.group(
			name="words",
			description="The words filter module."
	)
	async def words(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `words`.')
		
	@words.command(
			name="enable",
			description="Enables the words filter module.",
			aliases=["on"]
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def wordsenable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					await cursor.execute(
						"""
						INSERT INTO wordsautomod (guildid, toggle, words) VALUES ($1, $2, $3)
						""", ctx.guild.id, 1.0, "none",
					)

					await conn.commit()

					return await ctx.approve("Enabled the **words** automod module")

				if res[0] == 1:
					return await ctx.warn("The **words** automod module is already **enabled**.")

				await cursor.execute(
					"""
					UPDATE wordsautomod SET toggle = $1 WHERE guildid = $2
					""", 1.0, ctx.guild.id, 
				)

				await conn.commit()

				return await ctx.approve("Enabled the **words** filter module")

	@words.command(
			name="disable",
			description="Disables the invites filter module.",
			aliases=["off"]
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def wordsdisable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					return await ctx.warn("The **words** filter module is not configured in this guild.")

				if res[0] == 0:
					return await ctx.warn("The **words** filter module is already **disabled**.")

				await cursor.execute(
					"""
					UPDATE wordsautomod SET toggle = $1 WHERE guildid = $2
					""", 0, ctx.guild.id, 
				)

				await conn.commit()

				return await ctx.approve("Disabled the **words** filter module")

	@words.command(
			name="add",
			description="Blacklists a word for the words filter.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def wordsadd(self, ctx: StealContext, word:str):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				toggle = await cur.fetchone()

				if not toggle:
					return await ctx.warn("The **words** filter module is not configured in this guild.")

				if toggle[0] == 0:
					return await ctx.warn("The **words** filter module is **disabled**.")

				cur = await cursor.execute(
					"""
					SELECT words FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				words = await cur.fetchone()

				if words[0] == "none":
					print("AAAAAAAAAAAAAHHHH")
					formatted_word = word.strip().lower()
					formatted_word = "," + formatted_word + ","

					await cursor.execute(
						"""
						UPDATE wordsautomod SET words = $1
						""", formatted_word, 
					)
					await conn.commit()
					return await ctx.approve(f"Added **{word}** to the words filter.")


				things = [word for word in words[0].split(",")]

				print(things, "3")
				if word.strip() in things:
					return await ctx.warn(f"**{word}** is already in the **words** filter.")
				
				formatted_word = word.strip().lower()
				formatted_word = ',' + formatted_word + ","
				things.append(formatted_word)
				words = "".join(thing for thing in things)

				
				await cursor.execute(
					"""
					UPDATE wordsautomod SET words = $1 WHERE guildid = $2
					""", words, ctx.guild.id, 
				)

				await conn.commit()

				return await ctx.approve(f"Added **{word}** to the words filter.")
			
	@words.command(
			name="remove",
			description="Removes a word from the word filter"
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def wordsremove(self, ctx: StealContext, word:str):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM wordsautomod WHERE guildid = $1 
					""", ctx.guild.id
				)


				##### I WAS HERE DOING CLOSE CURSORS

				toggle = await cur.fetchone()

				if toggle:
					
					cur = await cursor.execute(
						"""
						SELECT words FROM wordsautomod WHERE guildid = $1
						""", ctx.guild.id
					)
					words = await cur.fetchone()
					things = [word for word in words[0].split(",") if word]
					if word.strip().lower() in things:
						things.remove(word.strip())
						words = "".join(thing for thing in things)
						await cursor.execute(
							"""
							UPDATE wordsautomod SET words = $1 WHERE guildid = $2
							""", words, ctx.guild.id, 
						)
						await cur.close()
						await conn.commit()
						return await ctx.approve(f"Removed **{word.strip()}** from the **words** filter.")
						
					return await ctx.warn(f"**{word}** is not in the **words** filter.")

	@words.command(
			name="config",
			description="Sends the words filter module config.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def wordsconfig(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				
				if res is None:
					return await ctx.warn("The **words** filter module is not configured in this guild.")


				cur = await cursor.execute(
					"""
					SELECT words  FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				toggle_converter = {
					1 : "enabled",
					0 : "disabled",
				}

				toggle = toggle_converter.get(res[0], "❓")

				words = await cur.fetchone()

				if words:
					if not words[0]:
						return await ctx.warn(f"The **words** filter is **{toggle}** with no filtered **words**.")

				wordlist = [word for word in words[0].split(",") if word]

				count = 0
				embeds = []

				entries = [
						f"`{i}` **{tagname.lower()}**"
						for i, tagname in enumerate(wordlist, start=1)
					]


				l = 5

				embed = discord.Embed(
					color=Colors.BASE_COLOR,
					description=f"{ctx.author.mention}: The **invites** filter module is **{toggle}**\n\n**Words**\n",
					title=f"Tags (`{len(entries)}`)",
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
							title=f"Tags (`{len(entries)}`)",
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


	@words.command(
			name="clear",
			description="Clears the words filter module config.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def wordsclear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words)
					""",				
				)

				cur = await cursor.execute(
					"""
					SELECT toggle FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)

				res = await cur.fetchone()

				if not res:
					return await ctx.warn("The **words** filter module is not configured in this guild.")

				await cur.execute(
					"""
					DELETE FROM wordsautomod WHERE guildid = $1
					""", ctx.guild.id, 
				)
				
				await conn.commit()

				return await ctx.approve(f"Cleared the **words** filter module.")
			

async def setup(bot):
	await bot.add_cog(Automod(bot))