from __future__ import print_function, annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import asyncio
from discord.ui import *
from sklearn import *
from tools.Steal import Steal
from managers.context import StealContext

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


	@managechannels.command(
			name='nuke',
			description='Nukes a channel.',
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def nukechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
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

	@managechannels.command(
			name='hide',
			description='Hides a channel from a user/role.',
			aliases=["remove"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def hidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), target:Optional[Union[discord.Role, discord.Member]] = commands.param(default=None, displayed_default=None)):
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

	@managechannels.command(
			name='reveal',
			description='Reveals a channel to a user/role.',
			aliases=["add", "show"]
	)
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def revealchannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None), target: Optional[Union[discord.Member, discord.Role]] = commands.param(default=None, displayed_default=None)):
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role
		perms = channel.overwrites_for(target)
		if perms.view_channel is False:
			perms = target.guild_permissions
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
	async def renamechannel(self, ctx: StealContext, name:str, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		if not channel:channel=ctx.channel
		try:
			await asyncio.wait_for(channel.edit(name=name, reason=f'Executed by {ctx.author}'), timeout=2)
			channel = await ctx.guild.fetch_channel(channel.id)
			return await ctx.approve(f'Renamed {channel.mention} to `{channel.name}`.')
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
	async def lockchannel(self, ctx: StealContext, target:Optional[Union[discord.Member, discord.Role]] = None, reason:Optional[str] = commands.param(default="No reason.", displayed_default=None), channel:Optional[discord.abc.GuildChannel] = None):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel
		if target is None: target = ctx.guild.default_role

		if isinstance(channel, Union[discord.ForumChannel, discord.Thread]):
			await channel.edit(locked=True, archived=True)
			return await ctx.approve(f"Locked {channel.mention} for {ctx.guild.default_role} - **{reason.split(' |')[0]}**")

		perms = channel.overwrites_for(target)

		if perms.send_messages is None or perms.send_messages is True:
			perms = target.guild_permissions if isinstance(target, discord.Member) else target.permissions
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
			overwrite.send_messages = False
			await channel.set_permissions(target=target, send_messages=False, reason=reason)
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
	async def unlockchannel(self, ctx: StealContext, target:Optional[Union[discord.Member, discord.Role]] = None, reason:Optional[str] = commands.param(default="No reason.", displayed_default=None), channel:Optional[discord.abc.GuildChannel] = None):
		reason += ' | Executed by {}'.format(ctx.author)
		if channel is None: channel = ctx.channel	
		if target is None: target = ctx.guild.default_role

		if isinstance(channel, Union[discord.ForumChannel, discord.Thread]):
			await channel.edit(locked=False, archived=False)
			return await ctx.approve(f"Unlocked {channel.mention} for {ctx.guild.default_role} - **{reason.split(' |')[0]}**")

		perms = channel.overwrites_for(target)

		if perms.send_messages is False:
			perms = target.guild_permissions
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
			overwrite.send_messages = None
			await channel.set_permissions(target=target, overwrite=overwrite, reason=reason)
			await ctx.approve(f"Unlocked {channel.mention} - **{reason.split(' |')[0]}**.")
		else:
			await ctx.deny(f"{channel.mention} is already unlocked for {target.mention}.")			

	@command(name="slowmode",
		  description="Set a channel slowmode",
		  aliases=['sm']
	)
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	async def slowmode_set(self, ctx:StealContext, time, channel:Optional[discord.abc.GuildChannel] = commands.param(default=None, displayed_default=None)) -> None:
		if not channel:channel=ctx.channel
		def time_conv(time):
			try:
				return int(time[:-1]) * time_convert[time[-1]]
			except:
				return time
		seconds = time_conv(time.lower())
		await channel.edit(slowmode_delay=seconds, reason=f'Executed by {ctx.author}')
		await ctx.approve(f'{f"Set {channel.mention}s slowmode to `{time}`" if int(seconds) > 0 else f"Removed {channel}s slowmode."}')

async def setup(bot):
	await bot.add_cog(Channels(bot))
