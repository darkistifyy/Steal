from __future__ import print_function

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import asyncio
from discord.ui import *
import base64
import requests
from sklearn import *
import scipy.cluster

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from io import BytesIO
from sklearn.cluster import KMeans
from skimage.transform import rescale

import binascii
import struct
from PIL import Image
import numpy as np
from PIL import Image
from io import BytesIO
import scipy.cluster
import scipy.cluster.vq
import binascii

NUM_CLUSTERS = 5

def dom_color(img):
	my_bytes = BytesIO(img)
	my_bytes.seek(0)
	im = Image.open(my_bytes)
	
	im = im.convert('RGBA')
	im = im.resize((150, 150))
	
	ar = np.asarray(im)
	shape = ar.shape
	
	mask = ar[:, :, 3] > 0
	ar = ar[mask]
	
	ar = ar[:, :3].astype(float)
	
	codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)

	vecs, dist = scipy.cluster.vq.vq(ar, codes)
	counts, bins = np.histogram(vecs, len(codes))

	index_max = np.argmax(counts)
	peak = codes[index_max]
	colour = binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii')
	return colour

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
			return await interaction.message.edit(embed=discord.Embed(description=f"{Emojis.DENY} You have cancelled the deletion of {interaction.channel.mention}", color=Colors.DENY_COLOR), view=self)

class Utility(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot

	@command(name="avatar", description='Gets someones avatar.', aliases=['av', 'pfp'], usage='avatar [@user]')
	async def avatar(self, ctx: StealContext, member:Optional[discord.User]) -> None:
		if not member:member=ctx.author
		if not member.display_avatar:
			return await ctx.deny(f"**{member}** does not have an avatar.")

		avatarbytes = await member.display_avatar.read()
		dominant_color = dom_color(avatarbytes)

		from isHex import isHex

		if isHex(dominant_color):
			rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))
			await ctx.reply(embed=discord.Embed(title=f"{member.display_name}'s avatar", url=member.display_avatar.url, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])).set_image(url=member.display_avatar.url))
		

	@command(name="banner", description='Gets someones avatar.', usage='avatar [@user]')
	async def banner(self, ctx: StealContext, member:Optional[discord.User]) -> None:
		if not member:member=ctx.author
		user = await self.bot.fetch_user(member.id)
		if user.banner:

			bannerbytes = await user.banner.read()
			dominant_color = dom_color(bannerbytes)

			from isHex import isHex

			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))
				await ctx.reply(embed=discord.Embed(title=f"{user.display_name}'s banner", url=user.banner.url, color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2])).set_image(url=user.banner))
		else:
			return await ctx.send(embed=discord.Embed(
				title=f"{member.display_name}'s banner color: {user.accent_color}", color=user.accent_color
				))

	@command(name="members", description='Server members.')
	@guild_only()
	async def members(self, ctx: StealContext) -> None:
		await ctx.reply(embed=discord.Embed(description=f'There are `{len(ctx.guild.members)-len([i for i in ctx.guild.members if i.bot])}` members excluding bots.', color=Colors.BASE_COLOR).add_field(
			name='Members:',
			value=f'`{len(ctx.guild.members)}`'
		).add_field(
			name='Bots:',
			value=f'`{len([i for i in ctx.guild.members if i.bot])}`'
		))

	@group(name="channel", description="Manage channels.")
	async def managechannels(self, ctx: StealContext) -> None:
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `channel`.')

	@managechannels.command(name='delete', description='Deletes a channel.', usage='channel delete <channel>')
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def deletechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None) -> None:
		if not channel or channel == ctx.channel:
			bs = "\'"
			return await ctx.warn(f'{f"I couldn{bs}t find a channel with those parameters" if not channel else ""}. Would you like to delete {ctx.channel.mention}?', view=ChannelDeleteConfirm())
			
		
		if channel in ctx.guild.channels:
			await channel.delete(reason=f'Executed by {ctx.author}')
			return await ctx.approve(f"Deleted {channel.name}")
			
		await ctx.warn(f'{channel} is not a valid channel.')

	@managechannels.command(name='create', description='Creates a channel.', usage='channel create <name>')
	@cooldown(2, 5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def createchannel(self, ctx: StealContext, name:Optional[str]) -> None:

		channel = await ctx.guild.create_text_channel(name=name if name else "channel", reason=f'Executed by {ctx.author}')
		await ctx.approve(f'Created {channel.mention}.')

	@managechannels.command(name='rename', description='Renames a channel.', usage='channel rename <channel> <name>')
	@cooldown(2,5, commands.BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def renamechannel(self, ctx: StealContext, channel:discord.abc.GuildChannel,name:Optional[str]) -> None:
		#if not isinstance(channel, discord.GuildChannel):
		#    await ctx.reply(embed=discord.Embed(description=f'{channel} is not a valid channel.', color=Color.red()))
		#    return

		try:
			await asyncio.wait_for(channel.edit(name=name if name else "channel", reason=f'Executed by {ctx.author}'), timeout=2)
			return await ctx.approve(f'Renamed {channel.mention} to `{name if name else "channel"}`.')
		except asyncio.TimeoutError:
			return await ctx.warn(f'Could not rename {channel.mention}, bot is ratelimited.')

		except Exception as e:
			return await ctx.deny(description=f'Error:\n```{e}```')

	@managechannels.group(name='slowmode', description='Sets slowmodes.')
	async def slowmode(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `slowmode`.')

	@slowmode.command(name="set", description="Set a channel slowmode.", aliases=["add"], usage='channel slowmode set 10s [channel]')
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	async def slowmode_set(self, ctx:StealContext, time, channel:Optional[discord.abc.GuildChannel]) -> None:
		def time_conv(time):
			try:
				return int(time[:-1]) * time_convert[time[-1]]
			except:
				return time
		seconds = time_conv(time.lower())
		await channel.edit(slowmode_delay=seconds, reason=f'Executed by {ctx.author}')
		await ctx.approve(f"Set {channel}'s slowmode to {time}")

	@slowmode.command(name="remove", description="Set a channel slowmode.", aliases=["clear"], usage='channel slowmode remove [channel]')
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	async def slowmode_remove(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel]):
		await channel.edit(slowmode_delay=0, reason=f'Executed by {ctx.author}')
		await ctx.approve(f"Removed {channel}'s slowmode.")

	@command(name="userinfo", description="Gives userinfo.", aliases=["ui", "uinfo"], usage='userinfo [user]')
	@cooldown(1,15, commands.BucketType.user)
	async def userinfo(self, ctx:StealContext, member: Optional[discord.Member]) -> None:

		if not member:member = ctx.author

		timestamp1 = discord.utils.format_dt(member.created_at, style="F")
		
		timestamp2 = [discord.utils.format_dt(member.joined_at, style="F") if member.joined_at else "?"] if not isinstance(ctx.channel, discord.DMChannel) else "?"

		if not isinstance(member, discord.User):
			roles = member.roles[-1:0:-1]

			if roles:

				rolelist = f", ".join([r.mention for r in member.roles if r != ctx.guild.default_role])
				if len(rolelist) > 200:
					continuation_string = ("(+{numeric_number})")

					available_length = 150 - len(continuation_string)

					role_chunks = []
					remaining_roles = 0
					for r in roles:
						chunk = f"{r.mention},"
						chunk_size = len(chunk)
						if chunk_size < available_length:
							available_length -= chunk_size
							role_chunks.append(chunk)
						else:
							remaining_roles += 1
					role_chunks.append(continuation_string.format(numeric_number=remaining_roles))
					rolelist = "".join(role_chunks)
			else:
				rolelist = None
		else:
			rolelist = "?"

		info = discord.Embed(
			color=Colors.BASE_COLOR,
		).add_field(
			name=f'Created at:',
			value=f'{timestamp1}',
			inline=True
		).add_field(
			name='Joined at:',
			value=f'{timestamp2}',
			inline=True
		).add_field(
			name='Roles:',
			value=f'{rolelist}',
			inline=False
		)
		
		await ctx.send(
			embed=info.set_author(name=member, icon_url=member.display_avatar.url if member.display_avatar else None)
			)

	@group(name='server', description='Manages server.', aliases=['guild'])
	async def server(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `server`.')

	@server.command(name='icon', description='Changes server icon.', aliases=['pfp', 'logo'], usage="server icon <image/attatchment>")
	@has_permissions(manage_guild=True)
	@bot_has_guild_permissions(manage_guild=True)
	@guild_only()
	async def servericon(self, ctx: StealContext, image:Optional[discord.Attachment]) -> None:

		if image:
			bytes_image = await image.read()

		await ctx.guild.edit(icon=bytes_image if image else None, reason=f'Updated icon | Executed by {ctx.author}')
		return await ctx.approve(f"Updated guild icon.")

	@server.command(name='splash', description='Changes server splash.')
	@has_permissions(manage_guild=True)
	@bot_has_guild_permissions(manage_guild=True)
	@guild_only()
	async def serversplash(self, ctx: StealContext, image:Optional[discord.Attachment]) -> None:

		if image:
			bytes_image = await image.read()

		await ctx.guild.edit(splash=bytes_image if image else None, reason=f'Updated splash | Executed by {ctx.author}')
		return await ctx.approve("Updated guild splash.")

	@server.command(name='banner', description='Changes server banner.')
	@has_permissions(manage_guild=True)
	@bot_has_guild_permissions(manage_guild=True)
	@guild_only()
	async def serverbanner(self, ctx: StealContext, image:Optional[discord.Attachment]) -> None:

		if image:
			bytes_image = await image.read()

		await ctx.guild.edit(banner=bytes_image if image else None, reason=f'Updated banner | Executed by {ctx.author}')
		return await ctx.approve("Updated guild banner.")

	@group(name='emoji', description='Manage emojis.')
	async def emoji(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `emoji`.')
	
	@emoji.command(name="add", description="Adds an emoji.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojiadd(self, ctx: StealContext, emoji:discord.Attachment, emoji_name:Optional[str]=None):
		try:
			if not emoji_name: emoji_name = emoji.filename.split(".")[0]


			emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Created emoji {emoji}")
		except:
			return await ctx.deny(f"Could not create emoji {emoji_name}")

	@emoji.command(name="steal", description="Steals an emoji.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojisteal(self, ctx: StealContext, emoji:discord.PartialEmoji, emoji_name:Optional[str]=None):
		try:
			if not emoji_name: emoji_name = emoji.name


			emoji = await ctx.guild.create_custom_emoji(name=f"{emoji_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Stole emoji {emoji}")
		except:
			return await ctx.deny(f"Could not Steal emoji {emoji_name}")

	@emoji.command(name="delete", description="Deletes an emoji.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojidelete(self, ctx: StealContext, emoji:discord.PartialEmoji):
		try:
			if emoji in ctx.guild.emojis:
				await ctx.guild.delete_emoji(emoji)

				return await ctx.approve(f"Deleted emoji {emoji}")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not delete emoji {emoji}")
	
	@emoji.command(name='rename', description="Renames an emoji.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojirename(self, ctx:StealContext, emoji:discord.PartialEmoji, name:str):
		try:
			if emoji in ctx.guild.emojis:
				emoji = await ctx.guild.fetch_emoji(emoji.id)
				await emoji.edit(name=f"{name}")
				
				return await ctx.approve(f"Renamed {emoji} to '{name}'")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not rename emoji {emoji}")				

	@group(name='sticker', description='Manage emojis.')
	async def sticker(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `sticker`.')
	
	@sticker.command(name="add", description="Adds a sticker.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickeradd(self, ctx: StealContext, emoji:discord.Attachment, sticker_name:Optional[str]=None):
		try:
			if not sticker_name: sticker_name = emoji.filename.split(".")[0]


			sticker = await ctx.guild.create_sticker(name=f"{sticker_name}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Created sticker {sticker}")
		except:
			return await ctx.deny(f"Could not create sticker {sticker_name}")

	@emoji.command(name="steal", description="Steals a sticker.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickersteal(self, ctx: StealContext, sticker:discord.Sticker, sticker_name:Optional[str]=None):
		try:
			if not sticker_name: sticker_name = sticker.name


			emoji = await ctx.guild.create_sticker(name=f"{sticker}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Stole sticker {sticker}")
		except:
			return await ctx.deny(f"Could not steal sticker {sticker}")

	@emoji.command(name="delete", description="Deletes an emoji.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickerdelete(self, ctx: StealContext, sticker:discord.Sticker):
		try:
			if sticker in ctx.guild.stickers:
				await ctx.guild.delete_sticker(sticker)

				return await ctx.approve(f"Deleted emoji {sticker}")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not delete emoji {sticker}")
	
	@emoji.command(name='rename', description="Renames an emoji.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojirename(self, ctx:StealContext, emoji:discord.PartialEmoji, name:str):
		try:
			if emoji in ctx.guild.emojis:
				emoji = await ctx.guild.fetch_emoji(emoji.id)
				await emoji.edit(name=f"{name}")
				
				return await ctx.approve(f"Renamed {emoji} to '{name}'")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not rename emoji {emoji}")				

"""

Create sticker group and commands later.
Use above as baseplate

"""


async def setup(bot):
	await bot.add_cog(Utility(bot))