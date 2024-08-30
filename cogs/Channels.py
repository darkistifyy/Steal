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
	async def hidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Role, discord.Member]] = None):
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
	async def managerevealchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None, target: Optional[Union[discord.Member, discord.Role]] = None):
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if not perms.view_channel:
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
			overwrite.view_channel = None if channel.permissions_for(ctx.guild.default_role).view_channel else True
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
	async def lockchannel(self, ctx: StealContext,channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None, *, reason:Optional[str] = None):
		await self.managelockchannel(ctx, channel=channel, target=target, reason=reason)

	@managechannels.command(
			name='lock',
			description='Locks a channel.',
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def managelockchannel(self, ctx: StealContext,channel:Optional[discord.abc.GuildChannel] = None, target:Optional[Union[discord.Member, discord.Role]] = None, *, reason:Optional[str] = None):
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
		await self.manageunlockchannel(ctx, channel=channel, target=target, reason=reason)

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
			overwrite.send_messages =  None if channel.permissions_for(ctx.guild.default_role).send_messages else True
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

async def setup(bot):
	await bot.add_cog(Channels(bot))
