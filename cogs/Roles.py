from __future__ import print_function, annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import asyncio
from discord.ui import *
from sklearn import *
import asqlite

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional, Union
from tools.Config import Colors, Emojis
from tools.Validators import ValidHex
from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from tools.bytesio import dom_color, caption_image
from managers.context import StealContext

class Roles(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = "Server role commands."
		
	@group(
			name="role",
			description="Manage roles.",
			brief="role",
			extras= {"permissions": ["manage_roles"]},
	)
	async def userrole(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.plshelp()

	@userrole.command(
			name='add', 
			description='Adds a role', 
			brief="role add @someguy @admin lol",
			aliases=["apply", "give"],
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleadd(self, ctx: StealContext, member:discord.Member, role:discord.Role, *, reason: Optional[str] = "No reason.") -> None:
			reason += ' | Executed by {}'.format(ctx.author)
			if member.top_role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f"You cannot **manage** the **roles** of {member.mention}.")
			if member.top_role.position < role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny("You cannot **manage** this **role**.")
			if role in member.roles:
				return await ctx.warn(f'{member.mention} already has {role.mention}')
			await member.add_roles(
				role, reason=reason
			)
			return await ctx.approve(f"**Added** {role.mention} to {member.mention} - **{reason.split(' |')[0]}**")

	@userrole.command(
			name='remove', 
			description='Removes a role',
			brief="role remove @someguy @admin lol",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleremove(self, ctx: StealContext, member:discord.Member, role:discord.Role, reason: Optional[str] = "No reason.") -> None: 
			reason += ' | Executed by {}'.format(ctx.author)
			if member.top_role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f"You cannot **manage** the **roles** of {member.mention}.")
			if member.top_role.position < role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f"You cannot **manage** {role.mention}.")
			if not role in member.roles:
				return await ctx.warn(f'{member.mention} does not have {role.mention}')
			await member.remove_roles(
				role, reason=reason
			)
			return await ctx.approve(f"**Removed** {role.mention} from {member.mention} - **{reason.split(' |')[0]}**")

	@userrole.command(
			name='rename',
			description='Renames a role.',
			brief="role rename @newrole member",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def rolerename(self, ctx: StealContext, role:discord.Role, *, name:str) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')
		
		try:
			await asyncio.wait_for(role.edit(name=name, reason=f'Executed by {ctx.author}'), timeout=3)
			return await ctx.approve(f"**Renamed** {role.mention}")

		except asyncio.TimeoutError:
			return await ctx.warn(f'Could not rename {role.mention}, bot is ratelimited.')

	@userrole.command(
			name='addall',
			description='Adds role to all.',
			brief="role addall @member",
			extras= {"permissions": ["administrator"]},
	)
	@cooldown(1,120, commands.BucketType.guild)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleaddall(self, ctx: StealContext, role:discord.Role) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')
		mems = len([i for i in ctx.guild.members])
		applied = 0
		failed = 0
		for mem in ctx.guild.members:
			if mem.top_role.position > ctx.author.top_role.position:
				return
			if not role in mem.roles:
				await asyncio.sleep(0.7)
				try:
					await mem.add_roles(
						role, reason=f"Mass application | Executed by {ctx.author}"
					)
					applied += 1
				except:
					failed += 1
			else:
				failed += 1        

		embed = discord.Embed(title=f"__Mass Application__",description=f'{Emojis.APPROVE} Role applied: {role.mention}', color=Colors.BASE_COLOR).set_footer(
			icon_url=ctx.author.avatar.url,
			text=f'Command run by {ctx.author} || {ctx.author.id}'
			).add_field(
				name='Successful applications:',
				value=f'`{applied}/{mems}`',
				inline=False
				).add_field(
					name="Failed applications:",
					value=f'{failed}/{mems-applied}',
					inline=False
				)
		
		await ctx.reply(embed=embed)

	@userrole.command(
			name='removeall',
			description='Removes role from all',
			brief="role removeall @member",
			extras= {"permissions": ["administrator"]},
	)
	@cooldown(1,120, commands.BucketType.guild)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleremoveall(self, ctx: StealContext, role:discord.Role) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')
		mems = len([i for i in ctx.guild.members])
		removed = 0
		failed = 0
		for mem in ctx.guild.members:
			if mem.top_role.position > ctx.author.top_role.position:
				return
			if role in mem.roles:
				await asyncio.sleep(0.7)
				try:
					await mem.remove_roles(
						role, reason=f'Mass removal | Executed by {ctx.author}'
					)
					removed += 1
				except:
					failed += 1
			else:
				failed += 1        

		embed = discord.Embed(title=f"__Mass Removal__",description=f'{Emojis.APPROVE} Role removed: {role.mention}', color=Colors.BASE_COLOR).add_field(
				name='Successful removals:',
				value=f'`{removed}/{mems}`',
				inline=False
				).add_field(
					name="Failed removals:",
					value=f'{failed}/{mems-removed}',
					inline=False
				)
		await ctx.reply(embed=embed)        

	@userrole.command(
			name='hoist',
			description='Hoists or unhoists a role.',
			brief="role hoist @member",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def hoistrole(self, ctx: StealContext, role:discord.Role) -> None:
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')
		if role.hoist:
			await role.edit(hoist=False, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Dehoisted {role.mention}.")
		else:
			await role.edit(hoist=True, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Hoisted {role.mention}.")		

	@userrole.command(
			name='color',
			description='Sets a role color.',
			brief="role color @member #abcdef",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def colorrole(self, ctx: StealContext, role:discord.Role, hex:Optional[ValidHex] = None) -> None:
		if hex is None:
			return await ctx.approve(f"Hex **color** of {role.mention} - **{role.color}**")
		
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')

		rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
		await role.edit(color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]), reason=f'Executed by {ctx.author}')
		return await ctx.approve(f"Set **color** of {role.mention} - **#{hex}**")

	@userrole.command(
			name='icon',
			description='Sets a role icon.',
			brief="role icon @member <image>",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def roleicon(self, ctx: StealContext, role:discord.Role, image:Optional[Union[discord.Attachment, discord.PartialEmoji]] = None) -> None:

		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')
		
		if image is None:
			if role.display_icon:
				if not isinstance(role.display_icon, str):
					avatarbytes = await role.display_icon.read()
					
					return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s icon", url=role.display_icon.url, color=await self.bot.dominant_color(avatarbytes)).set_image(url=role.display_icon.url))
				return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s emoji: {role.display_icon}", color=Colors.BASE_COLOR))
			else: 
				return await ctx.warn(f"**Invalid Input Given**: `image/emoji is a required argument that is missing an attachment.`")
		else:

			icon = await image.read()

			await role.edit(display_icon=icon, reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Set the **display icon** of {role.mention}.")
	
	@userrole.command(
			name='emoji',
			description='Sets a role emoji.',
			brief="role icon @member <emoji>",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def roleemoji(self, ctx: StealContext, role:discord.Role, emoji:Optional[str] = None) -> None:

		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')

		if emoji is None:
			if role.display_icon:
				if not isinstance(role.display_icon, str):
					avatarbytes = await role.display_icon.read()

					return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s display icon", url=role.display_icon.url, color=await self.bot.dominant_color(avatarbytes)).set_image(url=role.display_icon.url))
				return await ctx.reply(embed=discord.Embed(title=f"{role.name}'s emoji : {role.display_icon}", color=Colors.BASE_COLOR))
			else: 
				return await ctx.warn(f"**Invalid Input Given**: `emoji is a required argument that is missing an attachment.`")
		else:

			if emoji.id:
				icon = await emoji.read()

				await role.edit(display_icon=icon, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Set the **display icon** of {role.mention}.")

			await role.edit(display_icon=icon, reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Set the **display icon** of {role.mention}.")

	@userrole.command(
			name='delete',
			description='Deletes a role.',
			brief="role delete @member",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def deleterole(self, ctx: StealContext, role:discord.Role) -> None:

		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')


		await role.delete(reason=f'Executed by {ctx.author}')
		return await ctx.approve(f"**Deleted** role - **{role.name}**")	

	@userrole.command(
			name='create',
			description='Creates a role.',
			brief="role create member",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def createrole(self, ctx: StealContext, name:Optional[str], hoist:Optional[bool] = False, hex:Optional[ValidHex] = None) -> None:

		rgb = None

		if hex:
			rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

		role = await ctx.guild.create_role(name=name if name else "new role", hoist=hoist, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]) if rgb else None, reason = f"Executed by {ctx.author}")
		await ctx.approve(f"**Created** role - {role.mention}.")

	@group(
			name="autorole",
			description="Autorole module.",
			aliases=["ar"],
			brief="autorole",
			extras= {"permissions": ["manage_roles"]},
	)
	async def autorole(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.plshelp()
	
	@autorole.command(
			name="set",
			description="Adds a role on member join.",
			brief="autorole set @member",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	async def autorole_add(self, ctx: StealContext, role: discord.Role):
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f"You cannot **manage** {role.mention}.")
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'I cannot **manage** {role.mention}.')
		
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS autorole(guildid INTEGER, roleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT roleid FROM autorole WHERE guildid = $1
					""", ctx.guild.id, 
				)

				roleid = await cur.fetchone()

				if roleid:
					await cursor.execute(
						"""
						UPDATE roleid SET roleid = $1 WHERE guildid = $2
						""", ctx.guild.id, role.id, 
					)
					await conn.commit()
					return await ctx.approve(f"Overwrote **autorole** to {role.mention}")
				
				await cursor.execute(
					"""
					INSERT INTO autorole (guildid, roleid) VALUES ($1, $2)
					""", ctx.guild.id, role.id, 
				)
				await conn.commit()
				return await ctx.approve(f"Set **autorole** to {role.mention}")
			
	@autorole.command(
			name="clear",
			description="Clears the autorole config.",
			brief="autorole clear",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	async def autorole_clear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS autorole(guildid INTEGER, roleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT roleid FROM autorole WHERE guildid = $1
					""", ctx.guild.id, 
				)

				roleid = await cur.fetchone()

				if roleid:
					await cursor.execute(
						"""
						DELETE FROM autorole WHERE guildid = $1
						""", ctx.guild.id,
					)
					await conn.commit()
					return await ctx.approve(f"Cleared **autorole** config.")
				
				return await ctx.warn("There is no **autorole** config set for this guild.")

	@autorole.command(
			name="config",
			description="Sends the autorole config.",
			brief="autorole config",
			extras= {"permissions": ["manage_roles"]},
	)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	async def autorole_config(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS autorole(guildid INTEGER, roleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT roleid FROM autorole WHERE guildid = $1
					""", ctx.guild.id, 
				)

				roleid = await cur.fetchone()

				if not roleid:
					return await ctx.warn("There is no **autorole** config set for this guild.")

				try:
					role = ctx.guild.get_role(roleid[0])
				except:
					return await ctx.warn(f"The **autorole** in this **guild** is configured to a **deleted role**.")

				return await ctx.neutral(f"The **autorole** in this **guild** is configured to {role.mention}")



async def setup(bot):
	await bot.add_cog(Roles(bot))