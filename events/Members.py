import discord
from discord.ext import commands
from dotenv import *
from discord.ext.commands import *
import asqlite

from tools.Steal import Steal



class Members(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		
	@Cog.listener("on_member_join")
	async def on_join_autorole_event(self, member:discord.Member) -> None:
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:
				cur = await cursor.execute(
					"""
					SELECT roleid FROM autorole WHERE guildid = $1 
					""", member.guild.id
				)

				roleid = await cur.fetchone()

				if roleid:
					try:
						role = member.guild.get_role(roleid[0])
					except:
						return
					await member.add_roles(role, reason="Autorole Add")

async def setup(bot):
	await bot.add_cog(Members(bot))