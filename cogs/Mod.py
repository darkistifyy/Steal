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
from tools.Validators import ValidTime

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
			aliases=['nick'],
			brief="nickname",
			extras= {"permissions": ["manage_nicknames"]},
	)
	async def nick(self, ctx: StealContext) -> None:
		if ctx.invoked_subcommand is None:
			return await ctx.plshelp()
		
	@nick.command(
			name='force',
			description='Forces a nickname onto a user.',
			brief='nickname force @someguy thatguy',
			extras= {"permissions": ["manage_nicknames"]},
		)
	@has_permissions(manage_nicknames=True)
	@bot_has_guild_permissions(manage_nicknames=True)
	@guild_only()
	async def nickforce(self, ctx: StealContext, member:discord.Member, *, nick:str=None) -> None:
		try:
			await member.edit(nick=nick, reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"**Forced** a **nickname** on {member.mention} - **{nick}**.")
		except:
			return await ctx.deny(f'**Failed** to **force** a **nickname** on {member.mention}.')

	@nick.command(
			name='set', 
			description='Sets your nickname.', 
			brief="nickname set awesomenickname",
			extras= {"permissions": ["manage_nicknames"]},
	)
	@has_permissions(manage_nicknames=True)
	@bot_has_guild_permissions(manage_nicknames=True)
	async def nickset(self, ctx: StealContext, *, nick:str = None) -> None:
		try:
			await ctx.author.edit(nick=nick, reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"**Set** your **nickname** - **{nick}**.")
		except:
			return await ctx.deny(f'**Failed** to **remove** your **nickname**.')
		
	@nick.command(
			name='remove', 
			description="Removes a user's nickname.", 
			brief='nickname remove @someguy',
			extras= {"permissions": ["manage_nicknames"]},
	)
	@has_permissions(manage_nicknames=True)
	@bot_has_guild_permissions(manage_nicknames=True)
	@cooldown(1,10, BucketType.user)
	async def nickremove(self, ctx: StealContext, member:Optional[discord.Member] = Author) -> None:
		try:
			if member.nick:
				await member.edit(nick=None, reason=f'Executed by {ctx.author}')
				return await ctx.approve(f"**Removed** the **nickname** for {member.mention}.")
			else:
				return await ctx.deny(f'{member.mention} does not have a **nickname**.')
		except:
			return await ctx.deny(f'**Failed** to remove the **nickname** for {member.mention}.')

	@command(
			name = "ban",
			aliases=["ub"],
			description='Bans a user.',
			brief = "userban @someguy lol",
			extras= {"permissions": ["ban_members"]},
	)
	@cooldown(1, 10, BucketType.user)
	@has_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	async def ban(self, ctx: StealContext, user: discord.User, *, reason: Optional[str] = "No reason.") -> None:
		reason += ' | Executed by {}'.format(ctx.author)

		member = ctx.guild.get_member(user.id)
		if not member:
			await ctx.guild.ban(user, reason=reason)
			return await ctx.approve(f"**Banned** {user} - **{reason.split(' |')[0]}**")
		if member == ctx.guild.owner:
			return await ctx.warn(f"You cannot **ban** the **server owner**.")
		if member == ctx.author:
			return await ctx.warn(f"You cannot **ban yourself**.")
		if ctx.author.top_role.position <= member.top_role.position:
			return await ctx.warn(f"You cannot **ban** a user with a **higher role** than **yourself**.")
		
		await ctx.guild.ban(member, reason=reason)
		return await ctx.approve(f"**Banned** {user.mention} - **{reason.split(' |')[0]}**")
			
	@command(
			name='unban',
			description='Removes a ban.', 
			aliases=['unb'],
			brief="unban someguy.user lol",
			extras= {"permissions": ["ban_members"]},
	)
	@has_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def unban(self, ctx: StealContext, user:discord.User, *, reason: Optional[str] = "No reason.") -> None:
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			bans = [entry async for entry in ctx.guild.bans(limit=None)]
			if user in bans:
				return await ctx.deny(f'**{user}** is not **banned**.')

			await ctx.guild.unban(user, reason=reason) 
			return await ctx.approve(f'**Unbanned {user}** - **{reason.split(" |")[0]}**')
		except Exception as e:
			print(e)
			return await ctx.deny(f'**Failed** to **unban {user}**')

	@command(
			name = "kick",
			aliases = ["getout", "bye"],
			brief = "kick @someguy lol",
			extras= {"permissions": ["kick_members"]},
	)
	@cooldown(1, 10, BucketType.user)
	@has_permissions(kick_members=True)
	@bot_has_permissions(kick_members=True)
	async def kick(self, ctx: StealContext, user: discord.Member, *, reason: Optional[str] = "No reason.") -> None:
		reason += ' | Executed by {}'.format(ctx.author)

		try:
			if user.id == self.bot.user.id:
				return await ctx.deny("I cannot **mute** myself.")
			if user is ctx.guild.owner:
				return await ctx.deny(f"You cannot **kick** the server owner")
			if user is ctx.author:
				return await ctx.deny(f"You cannot **kick** yourself")
			if ctx.author.top_role.position <= user.top_role.position:
				return await ctx.deny(f"Unable - {user.mention} has role superiority over you")
			
			await user.kick(reason=reason)
			return await ctx.approve(f'**Kicked {user.mention}** - **{reason.split(" |")[0]}**')
		except:
			return await ctx.deny(f'**Failed** to **kick {user.mention}**.')

	@command(
			name='mute', 
			description='Mutes a user.', 
			aliases=["m"],
			brief="mute @someguy 10m lol",
			extras= {"permissions": ["manage_messages"]},
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(mute_members=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def mute(self, ctx: StealContext, user: discord.Member, time: ValidTime="5m", *, reason: Optional[str] = "No reason.") -> None:
		reason += ' | Executed by {}'.format(ctx.author)
		if user.id == self.bot.user.id:
			return await ctx.deny("I cannot **mute** myself")
		if user is ctx.guild.owner:
			return await ctx.deny(f"You cannot **mute** the server owner")
		if user is ctx.author:
			return await ctx.deny(f"You cannot **mute** yourself")
		if ctx.author.top_role.position <= user.top_role.position:
			return await ctx.deny(f"Unable - {user.mention} has role superiority over you")
		if ctx.permissions.manage_messages in user.guild_permissions:
			return await ctx.deny(f"{user.mention} cannot be **muted**")
			
		time = humanfriendly.parse_timespan(str(time))

		await user.timeout(discord.utils.utcnow() + datetime.timedelta(seconds=int(time)), reason=reason)

		if reason:
			await ctx.approve(f"**Muted** {user.mention} for `{humanfriendly.format_timespan(time)}` - **{reason.split(' |')[0]}**")
		
	@command(
			name='unmute', 
			description='Unmutes a member.', 
			aliases=["um"],
			brief='unmute @someguy lol',
			extras= {"permissions": ["manage_messages"]},
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(mute_members=True)
	@cooldown(1, 10, BucketType.user)
	@guild_only()
	async def unmute(self, ctx: StealContext, member:discord.Member, *, reason: Optional[str] = "No reason.") -> None:
		reason += ' | Executed by {}'.format(ctx.author)
		try:
			if member.is_timed_out():
				await member.timeout(None, reason=reason)
				return await ctx.approve(f"**Unmuted** {member.mention} - **{reason.split(' |')[0]}**")
				
			return await ctx.warn(f"{member.mention} is not **muted**.")
		except:
			return await ctx.deny(f"Failed to **unmute** {member.mention}")

	@command(
			name='purge',
			description='Purges messages.',
			aliases=['p', 'cleanup'],
			brief="purge 20",
			extras= {"permissions": ["manage_channel"]},
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@cooldown(1, 15, BucketType.channel)
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
			brief="pin",
			extras= {"permissions": ["manage_messages"]},
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def pin(self, ctx: StealContext, message:Optional[discord.Message]):
		if message is None:
			if ctx.message.reference:
				message = ctx.message.reference.resolved
			else:
				return await ctx.warn("Pass a **message link** or **reply** to one to **pin** it.")
		if message:
			if not message.pinned:
				await message.pin()
				return await ctx.message.add_reaction(
					Emojis.APPROVE
				)
			else:
				return await ctx.warn(f"That [**message**]({message.jump_url}) is already **pinned**.")
		else:
			return await ctx.warn("Pass a **message** or **reply** to one to **pin** it.")

	@command(
			name="unpin",
			description="Unpins a message by replying to it.",
			brief="unpin",
			extras= {"permissions": ["manage_messages"]},
	)
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def unpin(self, ctx: StealContext, message:Optional[discord.Message] = None):
		if message is None:
			if ctx.message.reference:
				message = ctx.message.reference.resolved
			else:
				return await ctx.warn("Pass a **message** or **reply** to one to **unpin** it.")
		if message is not None:
			if message.pinned:
				await message.unpin()
				await ctx.message.add_reaction(
					Emojis.APPROVE
				)
			else:
				await ctx.warn(f"That [**message**]({message.jump_url}) is not pinned.")
		else:
			await ctx.warn("Pass a **message** or **reply** to one to **unpin** it.")

	@command(
			name="quickpoll", 
			aliases=["poll"],
			description="Creates a quickpoll.",
			extras= {"permissions": ["manage_messages"]},
			brief='quickpoll "am i cool?" yes, no'
	)
	@guild_only()
	@has_permissions(manage_messages=True)
	@bot_has_guild_permissions(manage_messages=True)
	async def quickpoll(self, ctx: StealContext, question: str, *, answers:Union[str, list]):

		answers = [answer for answer in answers.split(",")]
		desc = []

		if len(answers) <= 1:
			return await ctx.warn("You need **more** than **1** answer.")

		if len(answers) > 10:
			return await ctx.warn("You **cannot** have **more** than **10** answers.")

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
			name="verification",
			description="The verification system.",
			aliases=["vrf", "verify"],
			brief="verification"
	)
	async def verification(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.plshelp()
	
	@verification.command(
			name="role",
			description="The role applied on user verification.",
			aliases=["r"],
			extras= {"permissions": ["manage_roles"]},
			brief="verification role @member"
	)
	@guild_only()
	@has_permissions(manage_roles=True)
	@bot_has_guild_permissions(administrator=True)
	async def verify_role(self, ctx: StealContext, role: discord.Role):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				if role.position > ctx.author.top_role.position or not ctx.author.top_role and ctx.author is not ctx.guild.owner:
					return await ctx.warn("You **cannot** set the **verification role** to a role **higher** than your **highest**..")


				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS verify(guildid INTEGER UNIQUE, roleid INTEGER)"
				)

				await db.execute(
					"REPLACE INTO verify (guildid, roleid) VALUES ($1, $2)",
#					"ON CONFLICT (guildid, roleid) DO UPDATE SET roleid = $2 WHERE guildid = $1",
					ctx.guild.id, role.id,
				)

				await db.commit()
				await cursor.close()

				await ctx.approve(f"Set the **verification role** to {role.mention}")

	@verification.command(
			name="config",
			description="The verification config.",
			aliases=["settings"],
			brief="verification config",
			extras= {"permissions": ["manage_channels"]},
	)
	@guild_only()
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(administrator=True)
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
				await cursor.close()

				if not row:
					return await ctx.warn("There is no **verification** config for this guild.")

				role = ctx.guild.get_role(row[1])

				if role:
					return await ctx.neutral(f"The **verification role** for this guild is set to {role.mention}.")
				return await ctx.warn("The **verification role** for this guild is set to an **invalid role**.")

	@verification.command(
			name='send',
			description='Creates a verification panel.', 
			aliases=['p', 'panel', 'panelcreate'],
			brief="verification send {title:verify here lol}",
			extras= {"permissions": ["manage_channels"]},
	)
	@guild_only()
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(administrator=True)
	@cooldown(1,120, commands.BucketType.guild)
	async def verifypanelsend(self, ctx: StealContext,  *, script:Optional[str] = None, channel:discord.TextChannel = None) -> None:
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
				await cursor.close()

				if not row:
					return await ctx.warn(f"There is no **verification role** set.")
				
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
