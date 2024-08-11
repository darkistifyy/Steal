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

	"""
	@managechannels.command(name='hide', description='Hides a channel.', usage='channel hide <channel>')
	@cooldown(2,5, BucketType.guild)
	@has_permissions(manage_channels=True)
	@bot_has_guild_permissions(manage_channels=True)
	@guild_only()
	async def hidechannel(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel] = None):
		if channel is None: channel = ctx.channel	
		perms = channel.overwrites_for(ctx.guild.default_role)
		if perms.view_channel is True:
			overwrites = {
				ctx.guild.default_role : discord.PermissionOverwrite(view_channel = False)
			}
			await channel.edit(overwrites=overwrites)
			await ctx.approve(f"Hidden {channel.mention}.")
		else:
			await ctx.deny(f"{channel.mention} is already hidden.")"""

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
	async def slowmode_remove(self, ctx: StealContext, channel:Optional[discord.abc.GuildChannel]) -> None:
		await channel.edit(slowmode_delay=0, reason=f'Executed by {ctx.author}')
		await ctx.approve(f"Removed {channel}'s slowmode.")

	@command(name="inviteinfo", description="Gives invite info.", aliases=["ii"])
	@cooldown(1,15, BucketType.user)
	async def inviteinfo(self, ctx: StealContext, invite: discord.Invite) -> None:

		invite_inviter = invite.inviter if invite.inviter else "Vanity URL."
		invite_channel = invite.channel.name
		invite_server_creation = discord.utils.format_dt(invite.guild.created_at)
		invite_server_creation_relative = discord.utils.format_dt(invite.guild.created_at, style="R")
		invite_creation_relative = discord.utils.format_dt(invite.created_at, style="R") if invite.created_at else "?"
		invite_server_verification = invite.guild.verification_level
		invite_server_boosts = invite.guild.premium_subscription_count
		invite_server_name = invite.guild.name

		if invite_server_boosts >= 3:
			level = 1
		if invite_server_boosts >= 7:
			level = 2
		if invite_server_boosts >= 14:
			level = 3
		if invite_server_boosts < 3:
			level = 0

		avatarbytes = await invite.guild.icon.read() if invite.guild.icon else None
		if avatarbytes is not None:
			dominant_color = dom_color(avatarbytes)
			from isHex import isHex
			if isHex(dominant_color):
				rgb = tuple(int(dominant_color[i:i+2], 16) for i in (0, 2, 4))

		embed = discord.Embed(
			description=f'{invite_server_creation} ({invite_server_creation_relative})',
			color=Color.from_rgb(r=rgb[0], g=rgb[1], b=rgb[2]) if avatarbytes else Colors.BASE_COLOR
		).add_field(
			name='Information',
			value=f'>>> Inviter: {invite_inviter}\nChannel: {invite_channel}\nCreated: {invite_creation_relative}',
			inline=True
		).add_field(
			name='Guild',
			value=f'>>> Name: {invite_server_name}\nNitro Boosts: {invite_server_boosts} (`Level {level}`)\nVerification Level: {invite_server_verification}',
			inline=True
		).set_author(
			name=f"{invite.id} ({invite.guild.id})",
			url=invite.url,
			icon_url=invite.guild.icon.url if invite.guild.icon else None
		)
		await ctx.send(embed=embed)

	@command(name="serverinfo", description="Gives server info.", aliases=["si"])
	@cooldown(1,15, BucketType.user)
	@guild_only()
	async def serverinfo(self, ctx: StealContext) -> None:

		server_owner = ctx.guild.owner
		server_verification = ctx.guild.verification_level
		server_boosts = ctx.guild.premium_subscription_count
		server_boost_level = ctx.guild.premium_tier
		server_members = round(len([i for i in ctx.guild.members]))
		server_members_formatted = (f"{server_members:,}")
		server_text_channels = len([channel for channel in ctx.guild.channels if isinstance(channel, discord.TextChannel)])
		server_voice_channels = len([channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)])
		server_roles = ctx.guild.roles[-1:0:-1]
		server_creation = discord.utils.format_dt(ctx.guild.created_at)
		server_creation_relative = discord.utils.format_dt(ctx.guild.created_at, style="R")
		if server_roles:
			role_list = f", ".join([r.mention for r in ctx.guild.roles if r != ctx.guild.default_role])
			if len(role_list) > 200:
				continuation_string = ("(+{numeric_number})")

				available_length = 150 - len(continuation_string)

				role_chunks = []
				remaining_roles = 0
				for r in server_roles:
					chunk = f"{r.mention},"
					chunk_size = len(chunk)
					if chunk_size < available_length:
						available_length -= chunk_size
						role_chunks.append(chunk)
					else:
						remaining_roles += 1
				role_chunks = role_chunks[::-1]
				role_chunks.append(continuation_string.format(numeric_number=remaining_roles))
				role_list = "".join(role_chunks)
		else:
			role_list = None
		
		embed = discord.Embed(
			description=f'{server_creation} ({server_creation_relative})',
			color=Colors.BASE_COLOR
		).add_field(
			name='Information',
			value=f'>>> Owner: {server_owner}\nVerification level: {str(server_verification)}\nNitro boosts: {str(server_boosts)} (`Level {str(server_boost_level)}`)',
			inline=True
		).add_field(
			name='Statistics',
			value=f'>>> Members: {server_members_formatted}\nText channels: {str(server_text_channels)}\nVoice channels: {str(server_voice_channels)}',
			inline=True
		).add_field(
			name='Roles',
			value=f'>>> {role_list}',
			inline=False
		).set_author(
			name=ctx.author,
			icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
		)
		await ctx.send(embed=embed)

	@command(name="userinfo", description="Gives userinfo.", aliases=["ui", "uinfo"], usage='userinfo [user]')
	@cooldown(1,15, commands.BucketType.user)
	async def userinfo(self, ctx:StealContext, member: Optional[discord.User]) -> None:

		if not member:member = ctx.author

		timestamp1 = discord.utils.format_dt(member.created_at, style="F")
		
		timestamp2 = [[discord.utils.format_dt(member.joined_at, style="F") if member.joined_at else "?"] if not isinstance(ctx.channel, discord.DMChannel) else "?"]

		if ctx.guild:
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
			value=f'{timestamp2[0]}',
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
	
	@emoji.command(name="add", description="Adds an emoji.", aliases=['create'])
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojiadd(self, ctx: StealContext, emoji:discord.Attachment, *, emoji_name:Optional[str]=None) -> None:
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
	async def emojisteal(self, ctx: StealContext, emoji:discord.PartialEmoji, *, emoji_name:Optional[str]=None) -> None:
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
	async def emojidelete(self, ctx: StealContext, emoji:discord.PartialEmoji) -> None:
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
	async def emojirename(self, ctx:StealContext, emoji:discord.PartialEmoji, *, name:str) -> None:
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

	@group(name='sticker', description='Manage emojis.')
	async def sticker(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `sticker`.')
	
	@sticker.command(name="add", description="Adds a sticker.", aliases=['create'])
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickeradd(self, ctx: StealContext, sticker:discord.Attachment, emoji:str, *, sticker_name:Optional[str]=None):
		await ctx.typing()
		try:
			if not sticker_name: sticker_name = sticker.filename.split(".")[0]


			sticker = await ctx.guild.create_sticker(name=f"{sticker_name}", image=await emoji.read(), emoji=f"{emoji}", reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Created sticker {sticker}")
		except:
			return await ctx.deny(f"Could not create sticker {sticker_name}")

	@sticker.command(name="steal", description="Steals a sticker.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickersteal(self, ctx: StealContext, sticker:discord.Sticker, sticker_name:Optional[str]=None):
		await ctx.typing()
		try:
			if not sticker_name: sticker_name = sticker.name


			emoji = await ctx.guild.create_sticker(name=f"{sticker}", image=await emoji.read(), reason=f'Executed by {ctx.author}')

			return await ctx.approve(f"Stole sticker {sticker}")
		except:
			return await ctx.deny(f"Could not steal sticker {sticker}")

	@sticker.command(name="delete", description="Deletes an sticker.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def stickerdelete(self, ctx: StealContext, sticker:discord.Sticker):
		await ctx.typing()
		try:
			if sticker in ctx.guild.stickers:
				await ctx.guild.delete_sticker(sticker)

				return await ctx.approve(f"Deleted sticker {sticker}")
			else:
				return await ctx.warn(f"That sticker is not from this server.")
		except:
			return await ctx.deny(f"Could not delete sticker {sticker}")
	
	@sticker.command(name='rename', description="Renames an sticker.")
	@has_permissions(manage_emojis=True)
	@bot_has_guild_permissions(manage_emojis=True)
	@guild_only()
	async def emojirename(self, ctx:StealContext, sticker:discord.Sticker, name:str):
		await ctx.typing()
		try:
			if sticker in ctx.guild.stickers:
				sticker = await ctx.guild.fetch_sticker(sticker.id)
				await sticker.edit(name=f"{name}")
				
				return await ctx.approve(f"Renamed {sticker} to '{name}'")
			else:
				return await ctx.warn(f"That emoji is not from this server.")
		except:
			return await ctx.deny(f"Could not rename sticker {sticker}") """

	@command(name='nitrohavers', description='Users with nitro.', aliases=['nhavers', 'nhs'], usage="nitrohavers")
	@guild_only()
	async def nhavers(self, ctx: StealContext) -> None:
		nhavers_ = []

		def guns(user:discord.Member):
			if isinstance(user, discord.Member):
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
	async def boosters(self, ctx: StealContext) -> None:
		boosters = [f"> {i_.mention} | {i_.id}\n" for i_ in ctx.guild.premium_subscribers]
		
		if not boosters:
			await ctx.reply(embed=discord.Embed(description=f"No boosters in `{ctx.guild}`", color=Color.red()))
			return        

		embed1 = discord.Embed(title='__Boosters__', description=f''.join(i for i in boosters), color=Color.pink()).set_author(icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None, name=ctx.author)
		await ctx.reply(embed=embed1)        

async def setup(bot):
	await bot.add_cog(Utility(bot))