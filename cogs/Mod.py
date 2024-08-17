from __future__ import annotations

import discord
from discord.ext import commands
from discord.ext.commands import *
from typing import Optional
import humanfriendly
import datetime

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
	def __init__(self, bot: Steal):
		self.bot = bot

	@group(
			name='nickname',
			description='Nicknames.',
			aliases=['nick']
	)
	async def nick(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `nick`.')
		
	@nick.command(
			name='force',
			description='Forces a nickname onto a user.',
		)
	@has_permissions(manage_nicknames=True)
	@bot_has_guild_permissions(manage_nicknames=True)
	@cooldown(1,10, BucketType.user)
	async def nickforce(self, ctx: StealContext, member:discord.Member, *, nick:Optional[str] = None):
		try:
			if nick is not None:
				await member.edit(nick=nick, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Forced {member.mention}'s nick - **{nick}**.")
			else:
				await member.edit(nick=nick, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Removed {member.mention}'s nick.")
		except:
			return await ctx.deny(f'Failed to force a nick on {member.mention}.')

	@nick.command(
			name='set', 
			description='Sets your nickname.', 
	)
	@has_permissions(manage_nicknames=True)
	@bot_has_guild_permissions(manage_nicknames=True)
	@cooldown(1,10, BucketType.user)
	async def nickset(self, ctx: StealContext, *, nick:Optional[str] = None):
		try:
			if nick is not None:
				await ctx.author.edit(nick=nick, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Set your nick - **{nick}**.")
			else:
				await ctx.author.edit(nick=nick, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Removed your nick.")
		except:
			return await ctx.deny(f'Failed to set your nick.')
		
	@nick.command(
			name='remove', 
			description="Removes a user's nickname.", 
	)
	@has_permissions(manage_nicknames=True)
	@bot_has_guild_permissions(manage_nicknames=True)
	@cooldown(1,10, BucketType.user)
	async def nickremove(self, ctx: StealContext, member:discord.Member):
		try:
			if member.nick:
				await member.edit(nick=None, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"Removed {member.mention}'s nick.")
			else:
				return await ctx.deny(f'{member.mention} does not have a nick..')
		except:
			return await ctx.deny(f'Failed to force a nick on {member.mention}.')

	@group(name='ban', description='Bans Members.')
	async def ban(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `ban`.')
		
	@ban.command(
			name = "add",
			description='Bans a user.',
	)
	@cooldown(1, 10, BucketType.user)
	@has_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	async def banadd(self, ctx: StealContext, user: discord.User, *, reason: Optional[str] = "no reason") -> None:
		reason += ' | Executed by {}'.format(ctx.author)

		try:
			if user not in ctx.guild.members:
				await ctx.guild.ban(user, reason=reason)
				return await ctx.approve(f"Successfully banned {user} - **{reason.split(' |')[0]}**")
			
			member = await ctx.guild.fetch_member(user)

			if member == ctx.guild.owner:
				return await ctx.warn(f"You're unable to ban the **server owner**.")
			if member == ctx.author:
				return await ctx.warn(f"You're unable to ban **yourself**.")
			if ctx.author.top_role.position <= member.top_role.position:
				return await ctx.warn(f"You're unable to ban a user with a **higher role** than **yourself**.")
			
			await ctx.guild.ban(member, reason=reason)
			return await ctx.approve(f"Successfully banned {user.mention} - **{reason.split(' |')[0]}**")
		except:
			return await ctx.deny(f'Failed to ban {user.mention}.')

	@ban.command(
			name='remove',
			description='Removes a ban.', 
			aliases=['revoke'], 
	)
	@has_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def banremove(self, ctx: StealContext, user:discord.User, *, reason: Optional[str] = 'No reason.') -> None:
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
	)
	@cooldown(1, 10, BucketType.user)
	@has_permissions(kick_members=True)
	@bot_has_permissions(kick_members=True)
	async def kick(self, ctx: StealContext, user: discord.Member, *, reason: Optional[str] = "No reason.") -> None:
		reason += ' | Executed by {}'.format(ctx.author)

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
		
	@group(
			name='mute',
			description='Mutes a member.'
	)
	async def mute(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `mute`.')

	@mute.command(
			name='add', 
		    description='Mutes a user.', 
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(mute_members=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def muteadd(self, ctx: StealContext, user: discord.Member, time: str="60s", *, reason: Optional[str] = "No reason.") -> None:
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
		
	@mute.command(
			name='remove', 
			description='Unmutes a member.', 
	)
	@has_permissions(moderate_members=True)
	@bot_has_guild_permissions(mute_members=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def muteremove(self, ctx: StealContext, member:discord.Member, *, reason: Optional[str] = 'No reason.') -> None:
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			if member.is_timed_out():
				await member.timeout(None, reason=reason)
				return await ctx.approve(f"Unmuted {member.mention} - {reason.split(' |')[0]}")
				
			return await ctx.warn(f"{member.mention} is not muted.")
		except:
			return await ctx.deny(f"Failed to unmute {member.mention}")

	@command(
			name='purge',
			description='Purges messages.',
			aliases=['p']
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@cooldown(1, 30, BucketType.user)
	@guild_only()
	async def purge(self, ctx: StealContext, number: Optional[int] = 5) -> None:
		if number <= 100 and ctx.author != ctx.guild.owner or ctx.author == ctx.guild.owner and number <= 200:
			await ctx.channel.purge(limit=number + 1, reason=f'Executed by {ctx.author}')
			embed=discord.Embed(
				color = Colors.BASE_COLOR,
		   		description = f'{Emojis.APPROVE} {ctx.author.mention}: Purged `{number}` messages.'
			)
			await ctx.send(embed=embed, delete_after=5.0)
		else:
			return await ctx.deny(f"Number of messages to purge must be **less** than `{'100' if ctx.author != ctx.guild.owner else '200'}`.")

	@command(
			name="pin",
			description="Pins a message by replying to it.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def pin(self, ctx: StealContext, message:Optional[discord.Message] = None):
		message = await ctx.channel.fetch_message(ctx.message.reference.message_id) or None if not message else message
		if message is not None:
			if message not in await ctx.channel.pins():
				await message.pin()
				await ctx.message.add_reaction(Emojis.APPROVE)
			else:
				await ctx.warn("That message is already pinned.")
		else:
			await ctx.warn("Pass a message or reply to pin it.")

	@command(
			name="unpin",
			description="Unpins a message by replying to it.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def unpin(self, ctx: StealContext, message:Optional[discord.Message] = None):
		message = await ctx.channel.fetch_message(ctx.message.reference.message_id) or None if not message else message
		if message is not None:
			if message in await ctx.channel.pins():
				await message.unpin()
				await ctx.message.add_reaction(Emojis.APPROVE)
			else:
				await ctx.warn("That message is not pinned.")
		else:
			await ctx.warn("Pass a message or reply to unpin it.")

async def setup(bot):
	await bot.add_cog(Mod(bot))
