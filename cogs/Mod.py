from __future__ import annotations

import discord
from discord.ext import commands
from discord.ext.commands import *
from typing import Optional, Union
import humanfriendly
import datetime
import asqlite
from tools.EmbedBuilder import EmbedBuilder
from tools.View import VerifyView

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
		self.description = "Server moderation commands."

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
	async def nickforce(self, ctx: StealContext, member:discord.Member, *, nick:Optional[str] = commands.param(default="No reason.", displayed_default=None)):
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
	async def nickset(self, ctx: StealContext, *, nick:Optional[str] = commands.param(default="No reason.", displayed_default=None)):
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
	async def banadd(self, ctx: StealContext, user: discord.User, *, reason: Optional[str] = commands.param(default="No reason.", displayed_default=None)) -> None:
		reason += ' | Executed by {}'.format(ctx.author)

		try:
			if user not in ctx.guild.members:
				await ctx.guild.ban(user, reason=reason)
				return await ctx.approve(f"Successfully banned {user} - **{reason.split(' |')[0]}**")
			
			member = ctx.guild.get_member(user.id)

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
	async def banremove(self, ctx: StealContext, user:discord.User, *, reason: Optional[str] = commands.param(default="No reason.", displayed_default=None)) -> None:
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
	async def kick(self, ctx: StealContext, user: discord.Member, *, reason: Optional[str] = commands.param(default="No reason.", displayed_default=None)) -> None:
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
	async def muteadd(self, ctx: StealContext, user: discord.Member, time: str="60s", *, reason: Optional[str] = commands.param(default="No reason.", displayed_default=None)) -> None:
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
	async def muteremove(self, ctx: StealContext, member:discord.Member, *, reason: Optional[str] = commands.param(default="No reason.", displayed_default=None)) -> None:
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			if member.is_timed_out():
				await member.timeout(None, reason=reason)
				return await ctx.approve(f"Unmuted {member.mention} - **{reason.split(' |')[0]}**")
				
			return await ctx.warn(f"{member.mention} is not **muted**.")
		except:
			return await ctx.deny(f"Failed to **unmute** {member.mention}")

	@command(
			name='purge',
			description='Purges messages.',
			aliases=['p']
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@cooldown(1, 30, BucketType.channel)
	@guild_only()
	async def purge(self, ctx: StealContext, number: Optional[int] = commands.param(default=5, displayed_default=None)) -> None:
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
	async def pin(self, ctx: StealContext, message:Optional[discord.Message] = commands.param(default=None, displayed_default=None)):
		if message is None:
			if ctx.message.reference:
				message = ctx.message.reference.resolved
			else:
				return await ctx.warn("Pass a message or reply to pin it.")
		if message is not None:
			if not message.pinned:
				await message.pin()
				await ctx.message.add_reaction(Emojis.APPROVE)
			else:
				await ctx.warn("That message is already pinned.")
		else:
			await ctx.warn("Pass a message or reply to unpin it.")

	@command(
			name="unpin",
			description="Unpins a message by replying to it.",
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def unpin(self, ctx: StealContext, message:Optional[discord.Message] = None):
		if message is None:
			if ctx.message.reference:
				message = ctx.message.reference.resolved
			else:
				return await ctx.warn("Pass a message or reply to unpin it.")
		if message is not None:
			if message.pinned:
				await message.unpin()
				await ctx.message.add_reaction(Emojis.APPROVE)
			else:
				await ctx.warn("That message is not pinned.")
		else:
			await ctx.warn("Pass a message or reply to unpin it.")

	@command(
			name="quickpoll", 
			aliases=["poll"],
			description="Creates a quickpoll."
	)
	async def quickpoll_cmd(self, ctx: StealContext, question: str, *, answers:Union[str, list]):

		answers = [answer for answer in answers.split(",")]
		desc = []

		if len(answers) <= 1:
			return await ctx.warn("You need more than 1 answer.")

		if len(answers) > 10:
			return await ctx.warn("You cannot have more than 10 answers.")

		reactions = {
				1 : "1️⃣",
				2 : "2️⃣",
				3 : "3️⃣",
				4 : "4️⃣",
				5 : "5️⃣",
				6 : "6️⃣",
				7 : "7️⃣",
				8 : "8️⃣",
				9 : "9️⃣",
				10 : "🔟"}

		number = 1
		for answer in answers:
			desc.append(f"{reactions.get(number)} - **{str(answer).replace('**', '')}**")
			number += 1

		message = await ctx.reply(
			embed=discord.Embed(
					color=Colors.BASE_COLOR,
					title=question,
					description="\n".join(desc)
				).set_author(
					name=ctx.author,
					icon_url=ctx.author.display_avatar.url
				)
		)

		number = 1
		for answer in answers:
			await message.add_reaction(reactions.get(number))
			number += 1

	@group(
			name="verify",
			description="The verification system.",
			aliases=["vrf", "verification"]
	)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(administrator=True)
	@guild_only()
	async def verify(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return
	
	@verify.command(
			name="role",
			description="The role applied on user verification.",
			aliases=["r"]
	)
	async def verify_role(self, ctx: StealContext, role: discord.Role):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS verify(guildid INTEGER UNIQUE, roleid INTEGER)"
				)

				await db.execute(
					"REPLACE INTO verify (guildid, roleid) VALUES ($1, $2)",
#					"ON CONFLICT (guildid, roleid) DO UPDATE SET roleid = $2 WHERE guildid = $1",
					ctx.guild.id, role.id,
				)

				await db.commit()

				await ctx.approve(f"Set the **verification role** to {role.mention}")

	@verify.command(
			name="config",
			description="The verification config.",
			aliases=["settings"]
	)
	async def verify_config(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS verify(guildid INTEGER UNIQUE, roleid INTEGER)"
				)

				cur = await db.execute(
					"SELECT * FROM verify WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **verification** config for this guild.")

				role = ctx.guild.get_role(row[1])

				if role:
					return await ctx.reply(f"The **verification role** for this guild is set to {role.mention}.")
				return await ctx.warn("The **verification role** for this guild is set to an invalid **role**.")

	@verify.command(
			name='send',
			description='Creates a verification panel.', 
			aliases=['p', 'panel', 'panelcreate'],
	)
	@guild_only()
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	@cooldown(1,120, commands.BucketType.guild)
	async def verifypanelsend(self, ctx: StealContext,  *, script:Optional[str] = commands.param(default=None, displayed_default=None), channel:discord.TextChannel = None) -> None:
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(		
					"CREATE TABLE IF NOT EXISTS verify(guildid INTEGER UNIQUE, roleid INTEGER)"
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM verify WHERE guildid = $1
					""", ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn(f"Please run the `{self.bot.command_prefix[0]}verify role` command before this one.")
				
				role = ctx.guild.get_role(row[1])

				if not role:
					return await ctx.warn(f"The **verification role** for this guild is **invalid**!.")

		if channel is None: channel = ctx.channel
		if not script:

			panelembed = discord.Embed(
				title='Verify',
				description='> Click on the **button** below to **verify**',
				color=Colors.BASE_COLOR,
			).set_author(
				name=ctx.guild.name,
				icon_url=ctx.guild.icon.url if ctx.guild.icon else None
			)

			await channel.send(embed=panelembed, view=VerifyView())
			return await ctx.approve(f'Sent default **verification** panel to {channel.mention}.', delete_after = 5.0)
		
		processed_message = EmbedBuilder.embed_replacement(ctx.author, script)
		content, embed, view = await EmbedBuilder.to_object(processed_message)

		await channel.send(content=content, embed=embed, view=VerifyView())
		return await ctx.approve(f'Sent **verification** panel to {channel.mention}.', delete_after = 5.0)

async def setup(bot):
	await bot.add_cog(Mod(bot))
