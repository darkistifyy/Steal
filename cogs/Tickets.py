from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import *
from discord import Color
from discord.ui import Button, View, button
from typing import Optional, Literal
import datetime
import asyncio

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis

embedgif = "https://media.discordapp.net/attachments/1243237867246063673/1262100449746485340/RainbowLine.gif?ex=66abc7a3&is=66aa7623&hm=c9256550e4b29785f6c89deb9db6ef472ee6450c82441bd39c5eaa29f74b942f&"

class TicketModPanel(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@button(label='🗑️', style=discord.ButtonStyle.gray, custom_id='ticketdelete')
	async def tickedelete(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer(ephemeral=True)

		for button in self.children:
			button.disabled = True

		await interaction.message.edit(view=self)

		await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} Deleting ticket in 5 seconds.', color=Colors.WARN_COLOR))

		await asyncio.sleep(5)

		await interaction.channel.delete()
	
	@button(label='🔓', style=discord.ButtonStyle.gray, custom_id='ticketreopen')
	async def ticketreopen(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer(ephemeral=True)

		for button in self.children:
			button.disabled = True

		tpic = interaction.channel.topic
		tpic1 = tpic.replace("Closed - ", "")
		tpic2 = tpic1.replace("Open - ", "")
		op = await interaction.guild.fetch_member(int(tpic2))

		if op in interaction.channel.members:
			return

		await interaction.message.edit(view=self)

		status = await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} Opening Ticket. . .', color=Colors.WARN_COLOR))

		overwrites = {
			interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel = False),
			op: discord.PermissionOverwrite(send_messages=True, view_channel=False),
			interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
		}

		try:
			await asyncio.wait_for(interaction.channel.edit(overwrites=overwrites,name=f"{op.name}", topic=f"Open - {op.id}"),timeout=2)
		except asyncio.TimeoutError:
			await interaction.channel.send(embed=discord.Embed(description=f"{Emojis.WARN} Rate limited. Skipping channel name change.",color=Colors.WARN_COLOR))
		except Exception as e:
			print(e)

		await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} Ticket opened successfully!', color=Colors.BASE_COLOR), view=TicketClose())
		await status.pin()

class TicketClose(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)
	
	@button(label='🔒', style=discord.ButtonStyle.danger, custom_id='ticketlock')
	async def ticketclose(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer(ephemeral=True)

		button.disabled = True
		await interaction.message.edit(view=self)

		if "Closed - " in interaction.channel.topic:
			return

		status = await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} Locking ticket. . .', color=Colors.WARN_COLOR))

		tpic = interaction.channel.topic
		tpic1 = tpic.replace("Closed - ", "")
		tpic2 = tpic1.replace("Open - ", "")
		op = await interaction.guild.fetch_member(int(tpic2))

		overwrites = {
			interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel = False),
			op: discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False),
			interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
		}


		try:
			await asyncio.wait_for(interaction.channel.edit(overwrites=overwrites,name=f"closed {op.name}", topic=f"Closed - {op.id}"),timeout=2)
		except asyncio.TimeoutError:
			await interaction.channel.send(embed=discord.Embed(description=f"{Emojis.WARN} Rate limited. Skipping channel name change.",color=Colors.WARN_COLOR))
		except Exception as e:
			print(e)

		await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} Ticket locked successfully!', color=Colors.BASE_COLOR), view=TicketModPanel())
		
class TicketCreate(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)
	
	@button(label='🎫',style=discord.ButtonStyle.blurple, custom_id='createticket')
	async def ticketcreate(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer(ephemeral=True)

		status = await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} Creating ticket. . .', color=Colors.WARN_COLOR), ephemeral=True)
		
		for ch in interaction.channel.category.text_channels:
			if f"Open - {interaction.user.id}" in ch.topic:
				await status.edit(embed=discord.Embed(description=f'{Emojis.WARN} You already have a ticket open in {ch.mention}.', color=Colors.WARN_COLOR))
				return

		overwrites = {
			interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
			interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel = True),
			interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
		}

		tc = await interaction.channel.category.create_text_channel(
			name=f'{interaction.user.name}',
			topic=f'Open - {interaction.user.id}',
			overwrites=overwrites
		)

		top = await tc.send(embed=discord.Embed(
			title='__Ticket opened.__',
			description='﹒Please explain why you opened this ticket\n﹒Be patient for a response.',
			color=Colors.BASE_COLOR
		).set_author(
			icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
			name=interaction.guild.name
		),view=TicketClose())
		await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} Ticket opened successfully: {tc.mention}', color=Colors.BASE_COLOR))
		await top.pin()

class Tickets(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
	
	@group(name="ticket", description='Tickets n stuff.')
	async def ticket(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `ticket`.')

	@ticket.command(name='panel', description='Creates a ticket panel.', aliases=['p', 'createpanel', 'panelcreate'], usage='ticket panel')
	@guild_only()
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	@cooldown(1,120, commands.BucketType.guild)
	async def create_panel(self, ctx: StealContext):
		tcg = await ctx.guild.create_category(name='◜ 🎫 ◞ @ TICKETS')
		tc = await tcg.create_text_channel(name='🎟﹒tickets', topic='Open tickets here.\nDo not move this channel from the bot created category.')
		
		panelembed = discord.Embed(
			title='__Open a ticket!__',
			description='﹒Click on the button below to create a ticket\n﹒Explain why you opened the ticket\n﹒Be patient for a response.',
			color=Color.pink(),
		).set_author(
			name=ctx.guild.name,
			icon_url=ctx.guild.icon.url if ctx.guild.icon else None
		).set_image(
			url=embedgif
		)

		await tc.send(embed=panelembed, view=TicketCreate())
		return await ctx.approve(f'Panel created successfully! {tc.mention}')

	@ticket.command(name='delete', description='Deletes a ticket.', aliases=['d', 'dt'], usage="ticket delete")
	@guild_only()
	@cooldown(1,5, commands.BucketType.channel)
	async def delete_ticket(self, ctx: StealContext):
		if ctx.channel.topic:
			if "Open - " in ctx.channel.topic or "Closed - " in ctx.channel.topic:
				await ctx.message.add_reaction(
					"✅"
				)
				await asyncio.sleep(5)
				await ctx.channel.delete()
				return
		
		await ctx.deny('This channel is not a ticket.')

	@ticket.command(name='close', description='Closes a ticket.', aliases=['lock', 'tc', 'tl'], usage='ticket close')
	@guild_only()
	@cooldown(1,5, commands.BucketType.channel)
	async def close_ticket(self, ctx: StealContext):

		tpic = ctx.channel.topic
		tpic1 = tpic.replace("Closed - ", "")
		tpic2 = tpic1.replace("Open - ", "")
		op = await ctx.guild.fetch_member(int(tpic2))

		if ctx.channel.topic and "Closed - " or "Open - " in ctx.channel.topic:
			if op in ctx.channel.members:
					status = await ctx.warn(f"Locking ticket. . .")

					overwrites = {
						ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel = False),
						op: discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False),
						ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
					}


					try:
						await asyncio.wait_for(ctx.channel.edit(overwrites=overwrites,name=f"closed {op.name}", topic=f"Closed - {op.id}"),timeout=2)
					except asyncio.TimeoutError:
						await ctx.channel.send(embed=discord.Embed(description="Rate limited. Skipping channel name change.",color=Color.red()))
					except Exception as e:
						print(e)

					return await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} Ticket locked successfully!', color=Colors.BASE_COLOR), view=TicketModPanel())
					
		
			else:
				return await ctx.deny('This ticket is already locked.')
						
		else:	
			return await ctx.deny('This channel is not a ticket.')		

	@ticket.command(name='open', description='Opens a ticket.', aliases=['unlock', 'to', 'tu'], usage="ticket open")
	@guild_only()
	@cooldown(1,5, commands.BucketType.channel)
	async def open_ticket(self, ctx: StealContext):

		tpic = ctx.channel.topic
		tpic1 = tpic.replace("Closed - ", "")
		tpic2 = tpic1.replace("Open - ", "")
		op = await ctx.guild.fetch_member(int(tpic2))

		if ctx.channel.topic and "Closed - " or "Open - " in ctx.channel.topic:
			if op in ctx.channel.members:
					status = await ctx.send(embed=discord.Embed(description=f'{Emojis.WARN} Opening ticket...', color=Colors.WARN_COLOR))

					overwrites = {
					ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel = False),
					op: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=False),
					ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
					}

					await ctx.channel.edit(topic=f"Open - {op.id}", overwrites=overwrites,)

					try:
						await asyncio.wait_for(ctx.channel.edit(name=f"{op.name}"),timeout=2)
					except asyncio.TimeoutError:
						await ctx.channel.send(embed=discord.Embed(description=f"{Emojis.WARN} Rate limited. Skipping channel name change.",color=Colors.WARN_COLOR()))
					except Exception as e:
						print(e)

					await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} Opened ticket.', color=Colors.BASE_COLOR), view=TicketClose())
					return
		
			if op in ctx.channel.members:
				return await ctx.warn('This ticket is already open.')
				
		else:
			return await ctx.warn('This channel is not a ticket.')	

async def setup(bot):
	await bot.add_cog(Tickets(bot))