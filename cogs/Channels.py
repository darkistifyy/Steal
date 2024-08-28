from __future__ import print_function, annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import asyncio
import asqlite
from discord.ui import *
import humanize.number
import humanize.time
from sklearn import *
from tools.Steal import Steal
from managers.context import StealContext
from tools.Validators import ValidTime
from tools.EmbedBuilder import EmbedBuilder
import humanize
import datetime

from typing import List, Optional, Union
from tools.Config import Colors, Emojis

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from typing import Generator, Union, Optional

import discord
from discord.ext import commands

from managers.context import StealContext

class ChannelDeleteConfirm(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@button(label="Confirm", emoji="✅", style=discord.ButtonStyle.green, custom_id="channeldeleteconfirm")
	async def channeldeleteconfirm(self,interaction:discord.Interaction, button:Button):
		await interaction.response.defer()
		for button in self.children:
			button.disabled=True
			await interaction.message.edit(view=self)

		await interaction.channel.delete(
			reason=f'Executed by {interaction.user}'
		)
	@button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, custom_id="channeldeletecancel")
	async def channeldeletecancel(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer()
		for button in self.children:
			button.disabled=True
			return await interaction.message.edit(embed=discord.Embed(description=f"{Emojis.DENY} {interaction.user.mention}: **Deletion** cancelled - {interaction.channel.mention}.", color=Colors.DENY_COLOR), view=self)
		
class ChannelNukeConfirm(discord.ui.View):
	def __init__(self, ctx: StealContext, channel: discord.abc.GuildChannel, bot: Steal):
		self.ctx = ctx
		self.channel = channel
		self.bot = bot
		super().__init__(timeout=None)

	@button(label="Confirm", emoji="✅", style=discord.ButtonStyle.green, custom_id="channelnukeconfirm")
	async def channeldeleteconfirm(self,interaction:discord.Interaction, button:Button):
		await interaction.response.defer()
		for button in self.children:
			button.disabled=True
			await interaction.message.edit(view=self)

		if isinstance(self.channel, Union[discord.ForumChannel, discord.Thread]):
			return await interaction.message.edit(
				embed=discord.Embed(
					description=f"{Emojis.WARN} {self.ctx.author.mention}: Unsupported channel type.",
					color=Colors.WARN_COLOR
				)
			)
	
		newchannelabc = await self.channel.clone(name=self.channel.name, reason=f"Nuke channel clone - {self.ctx.author}")
		newchannel = await self.ctx.guild.fetch_channel(newchannelabc.id)
		await self.channel.delete(reason=f'Nuke channel delete - {self.ctx.author}')
		if self.channel != self.ctx.channel: await self.ctx.approve(f"Nuked {self.channel.name}") 

		return await newchannel.send(
			embed=discord.Embed(
				description=f"{self.channel.name} was **nuked** by {self.ctx.author.mention}, this is the channel made to take its place.",
				color=Colors.BASE_COLOR
			).set_author(
				name=self.bot.user,
				icon_url=self.bot.user.display_avatar.url
			)
		)

	@button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, custom_id="channelnukecancel")
	async def channeldeletecancel(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer()
		for button in self.children:
			button.disabled=True
			return await interaction.message.edit(embed=discord.Embed(description=f"{Emojis.DENY} {self.ctx.author.mention}: **Nuking** cancelled - {interaction.channel.mention}.", color=Colors.DENY_COLOR), view=self)

class Channels(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = "Manage server channels."

	@group(
			name="channel",
			description="Manage channels."
	)
	async def managechannels(self, ctx: StealContext) -> None:
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `channel`.')

	@managechannels.command(
			name='delete',
			description='Deletes a channel.',
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def deletechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		if not channel or channel == ctx.channel:
			bs = "\'"
			return await ctx.warn(f'Would you like to delete {ctx.channel.mention}?', view=ChannelDeleteConfirm())
			
		
		if channel in ctx.guild.channels:
			await channel.delete(reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Deleted {channel.name}")
			
		await ctx.warn(f'{channel} is not a valid channel.')


	@command(
			name='nuke',
			description='Nukes a channel.',
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def nukechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		await self.managenukechannel(ctx,channel)

	@managechannels.command(
			name='nuke',
			description='Nukes a channel.',
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def managenukechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		if not channel: channel = ctx.channel
		return await ctx.warn(f'Are you sure you want to nuke {channel.mention}?', view=ChannelNukeConfirm(ctx, channel, self.bot))

	@managechannels.command(
			name='create',
			description='Creates a channel.',
	)
	@cooldown(2, 5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def createchannel(self, ctx: StealContext, *, name:Optional[str] = commands.param(default=None, displayed_default=None)) -> None:
		channel = await ctx.guild.create_text_channel(name=name if name else "channel", reason=f'Executed by {ctx.author}')
		await ctx.approve(f'Created {channel.mention}.')



	@command(
			name='hide',
			description='Hides a channel from a user/role.',
			aliases=["remove"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def hidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), target:Optional[Union[discord.Role, discord.Member]] = commands.param(default=None, displayed_default=None)):
		await self.managehidechannel(ctx,channel,target)	


	@managechannels.command(
			name='hide',
			description='Hides a channel from a user/role.',
			aliases=["remove"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def managehidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), target:Optional[Union[discord.Role, discord.Member]] = commands.param(default=None, displayed_default=None)):
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.view_channel is None or perms.view_channel is True:
			perms = target.guild_permissions if not isinstance(target, discord.Role) else target.permissions
			if isinstance(target, discord.Role):
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	

			overwrite = channel.overwrites_for(target)
			overwrite.view_channel = False
			await channel.set_permissions(target=target, overwrite=overwrite, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Hidden {channel.mention} from {target.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already hidden for {target.mention}.")

	@command(
			name='reveal',
			description='Reveals a channel to a user/role.',
			aliases=["add", "show"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def revealchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), target: Optional[Union[discord.Member, discord.Role]] = commands.param(default=None, displayed_default=None)):
		await self.managerevealchannel(ctx, channel, target)

	@managechannels.command(
			name='reveal',
			description='Reveals a channel to a user/role.',
			aliases=["add", "show"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def managerevealchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), target: Optional[Union[discord.Member, discord.Role]] = commands.param(default=None, displayed_default=None)):
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.view_channel is False:
			if isinstance(target, discord.Role):
				perms = target.permissions
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				perms = target.guild_permissions
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	
		
			overwrite = channel.overwrites_for(target)
			overwrite.view_channel = None
			await channel.set_permissions(target=target, overwrite=overwrite, reason=f'Executed by {ctx.author}')
			await ctx.approve(f"Revealed {channel.mention} to {target.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already visible to {target.mention}.")

	@managechannels.command(
			name='rename',
			description='Renames a channel.',
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def renamechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), *, name:str) -> None:
		if not channel:channel=ctx.channel
		if channel.name == name:
			return await ctx.warn("That's the same name.")
		try:
			await asyncio.wait_for(channel.edit(name=name, reason=f'Executed by {ctx.author}'), timeout=2)
			channel = await ctx.guild.fetch_channel(channel.id)
			return await ctx.approve(f'Renamed {channel.mention}.')
		except asyncio.TimeoutError:
			return await ctx.warn(f'Could not rename {channel.mention}, bot is ratelimited.')

		except Exception as e:
			return await ctx.deny(f'Error:\n```{e}```')

	@command(
			name='lock',
			description='Locks a channel.',
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def lockchannel(self, ctx: StealContext,channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None, *, reason:Optional[str] = commands.param(default="No reason.", displayed_default=None)):
		await self.managelockchannel(ctx, channel, target, reason)

	@managechannels.command(
			name='lock',
			description='Locks a channel.',
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def managelockchannel(self, ctx: StealContext,channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None, reason:Optional[str] = commands.param(default="No reason.", displayed_default=None)):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel
		if target is None: target = ctx.guild.default_role

		if isinstance(channel, Union[discord.ForumChannel, discord.Thread]):
			await channel.edit(locked=True, archived=True)
			return await ctx.approve(f"Locked {channel.mention} for {ctx.guild.default_role} - **{reason.split(' |')[0]}**")

		perms = channel.overwrites_for(target)

		if perms.send_messages is None or perms.send_messages is True:
			if isinstance(target, discord.Role):
				perms = target.permissions
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				perms = target.guild_permissions
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	


			overwrite = channel.overwrites_for(target)
			overwrite.send_messages = False
			await channel.set_permissions(target=target, overwrite=overwrite, reason=reason)
			await ctx.approve(f"Locked {channel.mention} for {target.mention} - **{reason.split(' |')[0]}**")
		else:
			await ctx.deny(f"{channel.mention} is already locked for {target.mention}.")

	@command(
			name='unlock',
			description='Unlocks a channel.',
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def unlockchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None, *, reason:Optional[str] = commands.param(default="No reason.", displayed_default=None)):
		await self.manageunlockchannel(ctx, channel, target, reason)

	@managechannels.command(
			name='unlock',
			description='Unlocks a channel.',
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def manageunlockchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None, reason:Optional[str] = commands.param(default="No reason.", displayed_default=None)):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role

		if isinstance(channel, Union[discord.ForumChannel, discord.Thread]):
			await channel.edit(locked=False, archived=False)
			return await ctx.approve(f"Unlocked {channel.mention} for {ctx.guild.default_role} - **{reason.split(' |')[0]}**")

		perms = channel.overwrites_for(target)

		if perms.send_messages is False:
			if isinstance(target, discord.Role):
				perms = target.permissions
				if target.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}.")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}.")			
				if not ctx.author == ctx.guild.owner:
					if target.position > ctx.author.top_role.position:
							return await ctx.warn(f"You cannot manage {target.mention}")								

			if isinstance(target, discord.Member):
				perms = target.guild_permissions
				if target == ctx.guild.owner:
					return await ctx.warn("You cannot manage the server owner.")
				if target.top_role.position > ctx.guild.me.top_role.position:
					return await ctx.warn(f"I cannot manage {target.mention}")
				if perms.manage_channels:
					return await ctx.warn(f"I cannot manage {target.mention}")	
				if not ctx.author == ctx.guild.owner:
					if target.top_role.position > ctx.author.top_role.position:
						return await ctx.warn(f"You cannot manage {target.mention}")	

			overwrite = channel.overwrites_for(target)
			overwrite.send_messages = None
			await channel.set_permissions(target=target, overwrite=overwrite, reason=reason)
			await ctx.approve(f"**Unlocked** {channel.mention} for {target.mention} - **{reason.split(' |')[0]}**")
		else:
			await ctx.deny(f"{channel.mention} is already **unlocked** for {target.mention}.")			

	@command(name="slowmode",
		  description="Set a channel slowmode",
		  aliases=['sm']
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	async def slowmode_set(self, ctx:StealContext, time:ValidTime, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		await self.channel_slowmode_set(ctx, time, channel)


	@managechannels.command(name="slowmode",
		  description="Set a channel slowmode",
		  aliases=['sm']
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	async def channel_slowmode_set(self, ctx:StealContext, time:ValidTime, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		if not channel:channel=ctx.channel
		await channel.edit(slowmode_delay=time, reason=f'Executed by {ctx.author}')
		await ctx.approve(f'{f"Set **slowmode** to **{humanize.precisedelta(datetime.timedelta(seconds=time))}** for {channel.mention}" if int(time) > 0 else f"Removed the **slowmode** for {channel.mention}."}')

	@group(
			name = "welcome",
			description="The welcoming members module.",
	)
	async def welcome(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `welcome`.')
	

	@welcome.command(
			name="channel",
			description="The channel to send welcome messages to.",
			aliases=["join"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomechannel(self, ctx: StealContext, channel:discord.TextChannel = None):
		if not channel: channel = ctx.channel

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					script = "{content:sup {user.mention}}"
					await cursor.execute(
						"INSERT INTO welcome (guildid, channelid, toggle, script) VALUES ($1, $2, $3, $4)",
						ctx.guild.id, channel.id, 1.0, script,
					)

					await db.commit()

					return await ctx.reply(
						embed=discord.Embed(
							description=f"> {Emojis.APPROVE} {ctx.author.mention}: Set the **welcome** channel to {channel.mention} with the script ```ruby\n{script}```",
							color=Colors.APPROVE_COLOR
						)
					)
				
				toggle = row[2]

				if toggle != 1:
					return await ctx.warn("The **welcome** module is **disabled**.")

				await cursor.execute(
					"UPDATE welcome SET channelid = $1 WHERE guildid = $2",
					channel.id, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve(f"Set the **welcome** channel to {channel.mention}.")

	@welcome.command(
			name="disable",
			description="Disables the welcome module",
			aliases=["off"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomedisable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				toggle = row[2]

				if toggle != 1:
					return await ctx.warn("The **welcome** module is already **disabled**")
				
				await cursor.execute(
					"UPDATE welcome SET toggle = $1 WHERE guildid = $2",
					0, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve("**Disabled** the **welcome** module.")

	@welcome.command(
			name="enable",
			description="Enables the welcome module",
			aliases=["on"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomeenable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				toggle = row[2]

				if toggle != 0:
					return await ctx.warn("The **welcome** module is already **enabled**")
				
				await cursor.execute(
					"UPDATE welcome SET toggle = $1 WHERE guildid = $2",
					1, ctx.guild.id, 
				)
				
				await db.commit()

				await ctx.approve("**Enabled** the **welcome** module.")

	@welcome.command(
			name="script",
			description="The script for the welcome message.",
			aliases=["code", "message"]
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomescript(self, ctx: StealContext, *, script: Optional[str] = None):
		if not script:
			default = "{content:sup {user.mention}}"

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("The **welcome** channel has not been configured for this guild.")
				
				if str(row[3]) == str(script if script else default):
					return await ctx.warn("That is the same **script** as before, not updating.")
				
				await cursor.execute(
					"UPDATE welcome SET script = $1",
					script if script else default,
				)

				await db.commit()

				await ctx.approve(f"Set **channel** module script to {'default' if not script else ''} ```ruby\n{script if script else default}```")

	@welcome.command(
			name="config",
			description="The config for the welcome module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomeconfig(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				channelid = row[1]
				channel = self.bot.get_channel(channelid)

				if channel:
					channel = channel.mention
				else:
					channel = "Invalid channel."

				toggle_converter = {
					1 : "enabled",
					0 : "disabled",
				}

				toggle = toggle_converter.get(row[2], "❓")

				script = row[3]

				await ctx.reply(
					embed=discord.Embed(
						title="Welcome config",
						color=Colors.BASE_COLOR
					).add_field(
						name="Channel",
						value=f"{channel}"
					).add_field(
						name="Toggle",
						value=f"{toggle.capitalize()}"
					).add_field(
						name="Script",
						value=f"```ruby\n{script}```",
						inline=False
					).set_author(
						name=ctx.guild.name,
						icon_url=ctx.guild.icon.url if ctx.guild.icon else None
					)
				)

	@welcome.command(
			name="test",
			description="Test the boost response module"
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcometest(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				channel = self.bot.get_channel(row[1])

				if not channel:
					return await ctx.warn("The **welcome** channel is invalid!")
				
				parsed = EmbedBuilder.embed_replacement(ctx.author, row[3])
				content, embed, view = await EmbedBuilder.to_object(parsed)
				
				await channel.send(content=content, embed=embed, view=None)	

	@welcome.command(
			name="clear",
			description="Clears the welcome module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def welcomeclear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **welcome** config set for this guild.")
				
				await cursor.execute(
					"DELETE FROM welcome WHERE guildid = $1",
					ctx.guild.id,
				)

				await db.commit()

				await ctx.approve("Cleared **welcome** module config.")

	@group(
			name = "boost",
			description="The boost response module.",
	)
	async def boost(self, ctx: StealContext):
		if not ctx.invoked_subcommand:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `boost`.')
	

	@boost.command(
			name="channel",
			description="The channel to send boost response messages to.",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostchannel(self, ctx: StealContext, channel:discord.TextChannel = None):
		if not channel: channel = ctx.channel

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:

				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					script = "{content:thanks for the boost {user.mention}}"
					await cursor.execute(
						"INSERT INTO boostresponse (guildid, channelid, toggle, script) VALUES ($1, $2, $3, $4)",
						ctx.guild.id, channel.id, 1.0, script,
					)

					await db.commit()

					return await ctx.reply(
						embed=discord.Embed(
							description=f"{Emojis.APPROVE} {ctx.author.mention}: Set **boost response** channel to {channel.mention} with the **script** ```{script}```",
							color=Colors.APPROVE_COLOR
						).set_footer(
							text=f"Use '{self.bot.command_prefix[0]}boost script <script>' to update the script.",
							icon_url=self.bot.user.display_avatar.url
						)
					)

				await cursor.execute(
					"UPDATE boostresponse SET channelid = $1 WHERE guildid = $2",
					channel.id, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve(f"Set **boost response** channel to {channel.mention}.")

	@boost.command(
			name="disable",
			description="Disables the boost response module",
			aliases=["off"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostdisable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				toggle = row[2]

				if toggle != 1:
					return await ctx.warn("The **boost response** module is already **disabled**")
				
				await cursor.execute(
					"UPDATE boostresponse SET toggle = $1 WHERE guildid = $2",
					0, ctx.guild.id, 
				)

				await db.commit()

				await ctx.approve("**Disabled** the **boost response** module.")

	@boost.command(
			name="enable",
			description="Enables the boost response module",
			aliases=["on"],
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostenable(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				toggle = row[2]

				if toggle != 0:
					return await ctx.warn("The **boost response** module is already **enabled**")
				
				await cursor.execute(
					"UPDATE boostresponse SET toggle = $1 WHERE guildid = $2",
					1, ctx.guild.id, 
				)
				
				await db.commit()

				await ctx.approve("**Enabled** the **boost response** module.")

	@boost.command(
			name="script",
			description="The script for the boost response message.",
			aliases=["code", "message"]
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostscript(self, ctx: StealContext, *, script: Optional[str]):
		if not script: default = "{content:thanks for the boost {user.mention}}"

		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("The **boost response** channel has not been configured for this guild.")
				
				if str(row[3]) == str(script if script else default):
					return await ctx.warn("That is the same script as before, not updating.")
				
				await cursor.execute(
					"UPDATE boostresponse SET script = $1",
					script if script else default,
				)

				await db.commit()

				await ctx.approve(f"Set **boost response** module script to {'default' if not script else ''} \n```ruby\n{default if not script else script}```")

	@boost.command(
			name="test",
			description="Test the boost response module"
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boosttest(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				channel = self.bot.get_channel(row[1])

				if not channel:
					return await ctx.warn("The **boost response** channel is invalid!")
				
				parsed = EmbedBuilder.embed_replacement(ctx.author, row[3])
				content, embed, view = await EmbedBuilder.to_object(parsed)
				
				await channel.send(content=content, embed=embed, view=None)	

	@boost.command(
			name="config",
			description="The config for the boost response module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostconfig(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				channelid = row[1]
				try:
					channel = self.bot.get_channel(channelid)
					channel = channel.mention
				except:
					channel = "Invalid channel"

				toggle_converter = {
					1 : "enabled",
					0 : "disabled",
				}

				toggle = toggle_converter.get(row[2], "❓")

				script = row[3]

				await ctx.reply(
					embed=discord.Embed(
						title="Boost response config",
						color=Colors.BASE_COLOR
					).add_field(
						name="Channel",
						value=f"{channel}"
					).add_field(
						name="Toggle",
						value=f"{toggle.capitalize()}"
					).add_field(
						name="Script",
						value=f"```ruby\n{script}```",
						inline=False
					).set_author(
						name=ctx.guild.name,
						icon_url=ctx.guild.icon.url if ctx.guild.icon else None
					)
				)

	@boost.command(
			name="clear",
			description="Clears the boost response module",
	)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_messages=True)
	@guild_only()
	async def boostclear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as db:
			async with db.cursor() as cursor:
				await cursor.execute(
					"CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
				)

				cur = await cursor.execute(
					"SELECT * FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **boost response** config set for this guild.")
				
				await cursor.execute(
					"DELETE FROM boostresponse WHERE guildid = $1",
					ctx.guild.id,
				)

				await db.commit()

				await ctx.approve("Cleared **boost response** module config.")





async def setup(bot):
	await bot.add_cog(Channels(bot))
