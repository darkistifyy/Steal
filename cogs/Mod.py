import discord
from discord import Color
from discord import ui
from discord.ui import Button,button, View
from discord.ext import commands
from discord.ext.commands import *
from datetime import timedelta
from typing import Optional, Literal
import asyncio
from typing import Optional
import humanfriendly
import datetime
from discord.ui import Button, View, button
import sqlite3

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

#class Confirm(View):
#	def __init__(self):
#		super().__init__(timeout=None)
#
#	@button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm_action")
#	async def verify(self, interaction:discord.Interaction, button:Button):
#
#		msg = await interaction.followup.send(embed=discord.Embed(title='Verifying...', description='> You are being verified...', color=Color.yellow()))

class Mod(commands.Cog):
	def __init__(self, Steal):
		self.bot = Steal

	@group(name='ban', description='Bans Members.')
	async def ban(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `ban`.')
		
	@ban.command(
		name = "add",
		description='Bans a user.',
		usage = "ban add @jpeg.dev raider"
	)
	@cooldown(1, 5, BucketType.user)
	@has_permissions(moderate_members=True)
	async def banadd(self, ctx: StealContext, user: discord.User, *, reason: str = "no reason"):
		reason += ' | Executed by {}'.format(ctx.author)
		await ctx.typing()

		try:
			if user not in ctx.guild.members:
				await ctx.guild.ban(user, reason=reason)
				return await ctx.approve(f"Successfully banned {user} - **{reason.split(" |")[0]}**")
			
			member = await ctx.guild.fetch_member(user)

			if member == ctx.guild.owner:
				return await ctx.warn(f"You're unable to ban the **server owner**.")
			if member == ctx.author:
				return await ctx.warn(f"You're unable to ban **yourself**.")
			if ctx.author.top_role.position <= member.top_role.position:
				return await ctx.warn(f"You're unable to ban a user with a **higher role** than **yourself**.")
			
			await ctx.guild.ban(member, reason=reason)
			return await ctx.approve(f'Successfully banned {user.mention} - **{reason.split(" |")[0]}**')
		except:
			return await ctx.deny(f'Failed to ban {user.mention}.')

	@ban.command(name='remove', description='Removes a ban.', aliases=['revoke'], usage='ban remove @jpeg.dev false ban')
	@has_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	@guild_only()
	async def banremove(self, ctx: StealContext, user:discord.User, *, reason: str = 'No reason.'):
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			bans = [entry async for entry in ctx.guild.bans(limit=None)]
			if user in bans:
				return await ctx.deny(f'{user} is not banned.')

			await ctx.guild.unban(user, reason=reason) 
			return await ctx.approve(f'Successfully unbanned **{user}** - **{reason.split(" |")[0]}**')
		except Exception as e:
			print(e)
			return await ctx.deny(f'Failed to unban **{user}**')

	@command(
		name = "kick",
		aliases = ["getout", "bye"],
		usage = "kick @jpeg.dev rule breaker"
	)
	@cooldown(1, 5, BucketType.user)
	@has_permissions(moderate_members=True)
	async def kick(self, ctx: StealContext, user: discord.Member, *, reason: str = "No reason."):
		reason += ' | Executed by {}'.format(ctx.author)
		await ctx.typing()

		try:
			if ctx.author is ctx.guild.owner:
				await user.kick(reason=reason)
				return await ctx.approve(f'Successfully kicked {user.mention} for {reason.split(" |")[0]}')
			if user is ctx.guild.owner:
				return await ctx.warn(f"You're unable to kick the **server owner**.")
			if user is ctx.author:
				return await ctx.warn(f"You're unable to kick **yourself**.")
			if ctx.author.top_role.position <= user.top_role.position:
				return await ctx.warn(f"You're unable to kick a user with a **higher role** than **yourself**.")
			
			await user.kick(reason=reason)
			return await ctx.approve(f'Successfully kicked **{user.mention}** - **{reason.split(" |")[0]}**')
		except:
			return await ctx.deny(f'Failed to kick **{user.mention}**.')
		
	@group(name='mute', description='Mutes a member.')
	async def mute(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `mute`.')

	@mute.command(name='add', description='Mutes a user.', brief='mute add @jpeg.dev raider', usage='mute add @jpeg.dev raider')
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(mute_members=True)
	@cooldown(1, 10, commands.BucketType.user)
	async def muteadd(self, ctx: StealContext, user: discord.Member, time: str="60s", *, reason: str = "No reason."):
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			if user.id == self.bot.user.id:
				return await ctx.deny("I cannot **mute** myself.")

			if user.id == ctx.author.id:
				return await ctx.deny("You cannot **mute** yourself.")

			member = ctx.guild.get_member(user.id)
			if member:

				if ctx.author.id != ctx.guild.owner_id:
					if member.top_role.position >= ctx.guild.me.top_role.position:
						return await ctx.warn("You cannot **mute** a member with a higher role than me.")
					if member.top_role.position >= ctx.author.top_role.position:
						return await ctx.warn("You cannot **mute** a member with a higher role than you.")
			else:
				pass
			
			time = humanfriendly.parse_timespan(time)

			await user.timeout(discord.utils.utcnow() + datetime.timedelta(seconds=time), reason=reason)

			if reason:

				await ctx.approve(f"Muted **{user}** for `{humanfriendly.format_timespan(time)}` - **{reason.split(' |')[0]}**")
		except:
			await ctx.deny(f"Failed to mute **{user}**")
		
	@mute.command(name='remove', description='Unmutes a member.', usage='mute remove @jpeg.dev false mute')
	@has_permissions(moderate_members=True)
	@bot_has_guild_permissions(moderate_members=True)
	@guild_only()
	async def muteremove(self, ctx: StealContext, member:discord.Member, reason: str = 'No reason.'):
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			if member.is_timed_out():
				await member.timeout(None, reason=reason)
				return await ctx.approve(f"Unmuted {member.mention} - {reason.split(' |')[0]}")
				
			return await ctx.warn(f"{member.mention} is not muted.")
		except:
			return await ctx.deny(f"Failed to unmute {member.mention}")
		
	@command(name='nitrohavers', description='Users with nitro.', aliases=['nhavers', 'nhs'], usage="nitrohavers")
	@guild_only()
	async def nhavers(self, ctx: StealContext):
		nhavers_ = []

		def guns(user:discord.Member):
			"""Guess if an user or member has Discord Nitro"""

			if isinstance(user, discord.Member):
			# Check if they have a custom emote in their status
				has_emote_status = any([a.emoji.is_custom_emoji() for a in user.activities if getattr(a, 'emoji', None)])
 
				return any([user.display_avatar.is_animated(), has_emote_status, user.premium_since, user.guild_avatar, user.banner])
		def get_nhavers():
			for i in ctx.guild.members:
				if not i.bot:
					if guns(i):
						nhavers_.append(f"{i.mention} | `{i.id}`\n")

		get_nhavers()
		if not nhavers_:
			await ctx.warn(f"No premium users in `{ctx.guild}`")
			return
		await ctx.neutral("".join(i for i in nhavers_))

	@command(name="boosters", description='Users server boosting.', usage='boosters')
	@guild_only()
	async def boosters(self, ctx: StealContext):
		boosters = [f"> <@{i_.id}> | {i_.id}\n" for i_ in ctx.guild.premium_subscribers]
		
		if not boosters:
			await ctx.reply(embed=discord.Embed(description=f"No boosters in `{ctx.guild}`", color=Color.red()))
			return        

		embed1 = discord.Embed(title='__Boosters__', description=f''.join(i for i in boosters), color=Color.pink()).set_footer(icon_url=ctx.author.avatar.url, text=f'Command run by {ctx.author} || {ctx.author.id}')
		await ctx.reply(embed=embed1)        

	@group(name="role", description="Manage roles.")
	async def userrole(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `role`.')

	@userrole.command(name='add', description='Adds a role', usage='role add @jpeg.dev @moderator new mod')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleadd(self, ctx: StealContext, member:discord.Member, role:discord.Role, reason: str = "No reason."):
			reason += ' | Executed by {}'.format(ctx.author)
			if member.top_role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny("You do not have permission to manage this users roles.")
			if member.top_role > ctx.guild.me.top_role:
				return await ctx.warn(f'Bot does not have permission to manage this user.')
			if role in member.roles:
				return await ctx.warn(f'{member.mention} already has {role.mention}')
			await member.add_roles(
				role, reason=reason
			)
			return await ctx.approve(f"Added {role.mention} to {member.mention} - {reason.split(' |')[0]}")

	@userrole.command(name='remove', description='Removes a role', usage='role remove @jpeg.dev @moderator mod abuse')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleremove(self, ctx: StealContext, member:discord.Member, role:discord.Role, reason: str = "No reason."): 
			reason += ' | Executed by {}'.format(ctx.author)
			if member.top_role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
				return await ctx.deny(f'You do not have permission to manage this users roles.')
			if member.top_role > ctx.guild.me.top_role:
				return await ctx.warn(f'Bot does not have permission to manage this user.')
			if not role in member.roles:
				return await ctx.warn(f'{member.mention} does not have {role.mention}')
			await member.remove_roles(
				role, reason=reason
			)
			return await ctx.approve(f"Removed {role.mention} from {member.mention} - {reason.split(' |')[0]}")

	@userrole.command(name='rename', description='Renames a role.', usage='role renmae @newrole @admin')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def rolerename(self, ctx: StealContext, role:discord.Role, *,name:str):
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny('You do not have permission to manage this role.')
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'Bot does not have permission to manage this role.')
		
		try:
			await asyncio.wait_for(role.edit(name=name, reason=f'Executed by {ctx.author}'), timeout=3)
			return await ctx.approve(f"Renamed {role.mention} to **{name}**")

		except asyncio.TimeoutError:
			return await ctx.warn(f'Could not rename {role.mention}, bot is ratelimited.')

	@userrole.command(name='addall', description='Adds role to all.', usage="role addall @member")
	@cooldown(1,120, commands.BucketType.guild)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleaddall(self, ctx: StealContext, role:discord.Role):
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny('You do not have permission to manage this role.')
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'Bot does not have permission to manage this role.')
		mems = len([i for i in ctx.guild.members])
		applied = 0
		failed = 0
		for mem in ctx.guild.members:
			if not role in mem.roles:
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
				value=f'`{applied}`',
				inline=False
				).add_field(
					name="Failed applications:",
					value=f'{failed}',
					inline=False
				).add_field(
					name="Server membercount:",
					value=f"{mems}",
					inline=False
				)
		
		await ctx.reply(embed=embed)

	@userrole.command(name='removeall', description='Removes role from all', usage='role removeall @member')
	@cooldown(1,120, commands.BucketType.guild)
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def roleremoveall(self, ctx: StealContext, role:discord.Role):
		if role.position > ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny('You do not have permission to manage this role.')
		if role.position > ctx.guild.me.top_role.position:
			return await ctx.warn(f'Bot does not have permission to manage this role.')
		mems = len([i for i in ctx.guild.members])
		removed = 0
		failed = 0
		for mem in ctx.guild.members:
			if role in mem.roles:
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
				value=f'`{removed}`',
				inline=False
				).add_field(
					name="Failed removals:",
					value=f'{failed}',
					inline=False
				).add_field(
					name="Server membercount:",
					value=f"{mems}",
					inline=False
				)
		await ctx.reply(embed=embed)        

	@userrole.command(name='hoist', description='Hoists or unhoists a role.', usage='role hoist @moderator')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def hoistrole(self, ctx: StealContext, role:discord.Role):
		await role.edit(hoist=False if role.hoist else True, reason=f'Executed by {ctx.author}')
		await ctx.approve(f"Hoisted {role.mention}")

	@userrole.command(name='color', description='Sets a role color.', usage='role color @moderator #hexcode')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def colorrole(self, ctx: StealContext, role:discord.Role, hex:str):
		import regex as re
		from isHex import isHex, isHexLower, isHexUpper
		
		if role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
			return await ctx.deny(f'You do not have permission to manage {role.mention}.')

		hex = hex.lstrip("#")
		if isHex(hex):
			rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
			await role.edit(color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]), reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Set {role.mention}'s color to `{hex}`")
		else:
			return await ctx.deny(f"`{hex}` is not a valid hex code.")

	@userrole.command(name='delete', description='Deletes a role.', usage='role delete @newrole')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def deleterole(self, ctx: StealContext, role:discord.Role):
		if role.position >= ctx.author.top_role.position:
			return await ctx.deny(f'You do not have permission to manage {role.mention}.')

		await role.delete(reason=f'Executed by {ctx.author}')
		return await ctx.approve(f"Deleted  {role.name}")	

	@userrole.command(name='create', description='Creates a role.')
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(manage_roles=True)
	@guild_only()
	async def createrole(self, ctx: StealContext, name:Optional[str]):
		role = await ctx.guild.create_role(name=name if name else "new role", reason = f"Executed by {ctx.author}")
		await ctx.approve(f"Created role {role.mention}.")

	@command(name='purge', description='Purges messages.')
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def purge(self, ctx: StealContext, number: Optional[int] = 5):
		if number <= 100:
			await ctx.channel.purge(limit=number + 1)
			await ctx.approve(f"Purged {number} messages.")
		else:
			return await ctx.deny("Number of messages to purge must be **less** than `100`.")

async def setup(bot):
	await bot.add_cog(Mod(bot))