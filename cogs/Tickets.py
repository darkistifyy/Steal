from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import *
from discord import Color
from discord.ui import Button, View, button
from tools.EmbedBuilder import EmbedBuilder, EmbedScript
from tools.EmbedBuilderUi import EmbedEditor, Embed
import asyncio
import asqlite

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

		await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} Deleting **ticket** in 5 seconds.', color=Colors.WARN_COLOR))

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

		status = await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} **Opening** Ticket. . .', color=Colors.WARN_COLOR))

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

		await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} **Opened** ticket.', color=Colors.BASE_COLOR), view=TicketClose())
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

		status = await interaction.followup.send(embed=discord.Embed(description=f'{Emojis.WARN} **Locking** ticket. . .', color=Colors.WARN_COLOR))

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

		await status.edit(embed=discord.Embed(description=f'{Emojis.APPROVE} **Locked** ticket.', color=Colors.BASE_COLOR), view=TicketModPanel())
		
class TicketCreate(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)
	
	@button(label='🎫',style=discord.ButtonStyle.blurple, custom_id='createticket')
	async def ticketcreate(self, interaction:discord.Interaction, button:Button):
		await interaction.response.defer(ephemeral=True)

		status = await interaction.followup.send(embed=discord.Embed(description=f'> {Emojis.WARN} **Creating** ticket. . .', color=Colors.WARN_COLOR), ephemeral=True)

		for ch in interaction.guild.text_channels:
			if f"Open - {interaction.user.id}" in ch.topic if ch.topic else False:
				await status.edit(embed=discord.Embed(description=f'> {Emojis.WARN} You already have a **ticket** open in {ch.mention}.', color=Colors.WARN_COLOR))
				return

		overwrites = {
			interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
			interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel = True),
			interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
		}

		
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:
				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", interaction.guild.id
				) 

				row = await cur.fetchone()

				if row:
					sup = interaction.guild.get_role(row[3])
					cat = interaction.guild.get_channel(row[1])
					openscript = row[2] 
				else:
					supportroleid = None
					categoryid = None
					openscript = None

				if sup:
					overwrites[sup] = discord.PermissionOverwrite(read_messages=True, send_messages=True)              

				
				if cat:
					tc = await cat.create_text_channel(
						name=f"{interaction.user.name}",
						topic=f"Open - {interaction.user.id}",
						overwrites=overwrites
					) if cat else await interaction.guild.create_text_channel(
							name=f'{interaction.user.name}',
							topic=f'Open - {interaction.user.id}',
							overwrites=overwrites
					)

#				if openscript is not None:

				parsed = EmbedBuilder.embed_replacement(interaction.user, openscript)
				content, embed, _ = await EmbedBuilder.to_object(parsed)

				out = await tc.send(content=content, embed=embed, view=TicketClose())
				await out.pin()

				return await status.edit(embed=discord.Embed(description=f'> {Emojis.APPROVE} **Ticket** opened: {tc.mention}', color=Colors.BASE_COLOR))
				
"""				top = await tc.send(embed=discord.Embed(
					title='__Ticket opened.__',
					description='﹒Please explain why you opened this ticket\n﹒Be patient for a response.',
					color=Colors.BASE_COLOR
				).set_author(
					icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
					name=interaction.guild.name
				),view=TicketClose())
				await status.edit(embed=discord.Embed(description=f'> {Emojis.APPROVE} Ticket opened: {tc.mention}', color=Colors.BASE_COLOR))
				await top.pin()"""
					



class Tickets(commands.Cog):
	def __init__(self, bot: Steal):
		self.bot = bot
		self.description = "Server ticket commands."
	
	@group(name="ticket", description='Tickets n stuff.')
	async def ticket(self, ctx: StealContext):
		if ctx.invoked_subcommand is None:
			return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `ticket`.')

	@ticket.command(
			name='send',
			description='Creates a ticket panel.', 
			aliases=['p', 'panel', 'panelcreate'],
	)
	@guild_only()
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	@cooldown(1,120, commands.BucketType.guild)
	async def panelsend(self, ctx: StealContext,  *, script:Optional[str] = commands.param(default=None, displayed_default=None), channel:discord.TextChannel = None) -> None:
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS tickets(guildid INTEGER, categoryid INTEGER, openscript TEXT, supportroleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn(f"Please run the `{self.bot.command_prefix[0]}ticket opened` command before this one.")

		if channel is None: channel = ctx.channel
		if not script:

			panelembed = discord.Embed(
				title='__Open a ticket!__',
				description='﹒Click on the **button** below to create a **ticket**\n﹒**Explain** why you opened the **ticket**\n﹒Be **patient** for a **response**.',
				color=Colors.BASE_COLOR,
			).set_author(
				name=ctx.guild.name,
				icon_url=ctx.guild.icon.url if ctx.guild.icon else None
			)

			await channel.send(embed=panelembed, view=TicketCreate())
			return await ctx.approve(f'Sent default **ticket** panel to {channel.mention}.')
		
		processed_message = EmbedBuilder.embed_replacement(ctx.author, script)
		content, embed, view = await EmbedBuilder.to_object(processed_message)

		await channel.send(content=content, embed=embed, view=TicketCreate())
		return await ctx.approve(f'Sent **ticket** panel to {channel.mention}.')

		"""
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
		return await ctx.approve(f'Panel created successfully! {tc.mention}')"""

	@ticket.command(
			name="opened",
			description="The script that sends when a ticket is opened.",
			aliases=["script", "setup"]
	)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	async def ticketopened(self, ctx: StealContext, *, script:Optional[str] = commands.param(default=None, displayed_default=None)):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS tickets(guildid INTEGER, categoryid INTEGER, openscript TEXT, supportroleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", ctx.guild.id, 
				)

				row = await cur.fetchone()

				if not script:
					default = """{embed}{color: #6a6a6a}{title: __Ticket opened__}{description: ﹒Please explain why you opened this ticket
﹒Be patient for a response.}{author: Test Server}"""

				if row:
					if row[2]:
						if not script:
							await cursor.execute(
								"""
								UPDATE tickets SET openscript = $1 WHERE guildid = $2
								""", default, ctx.guild.id, 
							)
							await conn.commit()
							return await ctx.approve(f"Set **ticket** opening script to default \n```ruby\n{default}```")

						await cursor.execute(
							"""
							UPDATE tickets SET openscript = $1 WHERE guildid = $2
							""", script, ctx.guild.id, 
						)

						await conn.commit()

						return await ctx.approve(f"Overwrote **ticket** opening script to\n```ruby\n{script}```")
				
				if not script:
					
					await cursor.execute(
						"""
						INSERT INTO tickets (guildid, categoryid, openscript, supportroleid) VALUES ($1, $2, $3, $4)
						""",ctx.guild.id, 0, default, 0, 
					)
					await conn.commit()
					await ctx.approve(f"Set **ticket** opening script to default\n```ruby\n{default}```")
					return

				await cursor.execute(
					"""
					INSERT INTO tickets (guildid, categoryid, openscript, supportroleid) VALUES ($1, $2, $3, $4)
					""", ctx.guild.id, 0, script, 0, 
				)
				await conn.commit()
				return await ctx.approve(f"Set **ticket** opening script to\n```ruby\n{script}```")

	@ticket.command(
			name="support",
			description="Sets the ticket support role."
	)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	async def ticketsupport(self, ctx: StealContext, role:discord.Role):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS tickets(guildid INTEGER, categoryid INTEGER, openscript TEXT, supportroleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", ctx.guild.id, 
				)

				row = await cur.fetchone()

				if row:

					if role.id == row[3]:
						return await ctx.warn("That is the same **script** as before, not updating.")

					await cursor.execute(
						"""
						UPDATE tickets SET supportroleid = $1 WHERE guildid = $2
						""", role.id, ctx.guild.id, 
					)

					await conn.commit()
					await ctx.approve(f"Overwrote **ticket** support role to {role.mention}")
					return
					
				return await ctx.warn(f"Please run the `{self.bot.command_prefix[0]}ticket opened` command before this one.")

	@ticket.command(
			name="category",
			description="Sets the ticket category."
	)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	async def ticketcategory(self, ctx: StealContext, category:discord.CategoryChannel):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS tickets(guildid INTEGER, categoryid INTEGER, openscript TEXT, supportroleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", ctx.guild.id, 
				)

				row = await cur.fetchone()

				if row:
					await cursor.execute(
						"""
						UPDATE tickets SET categoryid = $1 WHERE guildid = $2
						""", category.id, ctx.guild.id, 
					)
					await conn.commit()
					await ctx.approve(f"Set **ticket** category to **{category}**")
					return
				
				return await ctx.warn(f"Please run the `{self.bot.command_prefix[0]}ticket opened` command before this one.")
	@ticket.command(
			name="config",
			description="Config for the ticket module."
	)
	@has_permissions(manage_channels=True)
	async def ticketconfig(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS tickets(guildid INTEGER, categoryid INTEGER, openscript TEXT, supportroleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", ctx.guild.id
				)

				row = await cur.fetchone()

				if not row:
					return await ctx.warn("There is no **ticket** config set for this guild.")
				
				if row[1]:
					category = ctx.guild.get_channel(row[1])
					if not category:
						category = "Invalid category"
				else:
					category = "None"

				if row[3]:
					role = ctx.guild.get_role(row[3])
					if role:
						role = role.mention
					else:
						role = "Invalid role"
				else:
					role = "None"
				await ctx.send(
					embed=discord.Embed(
						title="Ticket config",
						color=Colors.BASE_COLOR,
						description=f">>> **Category**: {category}\n**Support role**: {role}"
					).add_field(
						name="Opening ticket embed",
						value=f"```ruby\n{row[2]}```",
					)
				)

	@ticket.command(
			name="clear",
			description="Clears the ticket config."
	)
	@has_permissions(administrator=True)
	@bot_has_guild_permissions(manage_channels=True)
	async def ticketclear(self, ctx: StealContext):
		async with asqlite.connect("main.db") as conn:
			async with conn.cursor() as cursor:

				await cursor.execute(
					"""
					CREATE TABLE IF NOT EXISTS tickets(guildid INTEGER, categoryid INTEGER, openscript TEXT, supportroleid INTEGER)
					"""
				)

				cur = await cursor.execute(
					"""
					SELECT * FROM tickets WHERE guildid = $1
					""", ctx.guild.id, 
				)

				res = await cur.fetchall()

				if res:
					await cursor.execute(
						"""
						DELETE FROM tickets WHERE guildid = $1
						""", ctx.guild.id, 
					)
					await conn.commit()
					await ctx.approve(f"Cleared **ticket** config.")
					return
				
			return await ctx.warn(f"There is no **ticket** config for this guild.")


	@ticket.command(
			name='delete', 
			description='Deletes a ticket.', 
			aliases=['d', 'dt'], 
	)
	@guild_only()
	@cooldown(1,5, commands.BucketType.channel)
	async def delete_ticket(self, ctx: StealContext) -> None:
		if ctx.channel.topic:
			if "Open - " in ctx.channel.topic or "Closed - " in ctx.channel.topic:
				await ctx.message.add_reaction(
					Emojis.APPROVE
				)
				await asyncio.sleep(5)
				await ctx.channel.delete()
				return
		
		await ctx.deny('This **channel** is not a **ticket**.')

	@ticket.command(
			name='close', 
			description='Closes a ticket.', 
			aliases=['lock', 'tc', 'tl'], 
	)
	@guild_only()
	@cooldown(1,5, commands.BucketType.channel)
	async def close_ticket(self, ctx: StealContext) -> None:

		tpic = ctx.channel.topic
		if tpic:
			tpic1 = tpic.strip("Closed - ")
			tpic2 = tpic1.strip("Open - ")
		else:
			return await ctx.deny('This **channel** is not a **ticket** or the **topic** has been changed.')
		op = await ctx.guild.fetch_member(int(tpic2))

		if ctx.channel.topic and "Closed - " or "Open - " in ctx.channel.topic:
			if op in ctx.channel.members or "Open - " in ctx.channel.topic:

					status = await ctx.send(embed=discord.Embed(description=f'> {Emojis.WARN} **Locking** ticket. . .', color=Colors.WARN_COLOR))

					async for message in ctx.channel.history(limit=None):
						if message.author.id == self.bot.user.id:
							if message.components:
								view = discord.ui.View.from_message(message)
								for child in view.children:
									child.disabled = True
								await message.edit(view=view)

					overwrites = {
						ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel = False),
						op: discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False),
						ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
					}

					await ctx.channel.edit(topic=f"Closed - {op.id}")

					try:
						await asyncio.wait_for(ctx.channel.edit(overwrites=overwrites,name=f"closed {op.name}"),timeout=2)
					except asyncio.TimeoutError:
						await ctx.channel.send(embed=discord.Embed(description="Rate limited. Skipping channel name change.",color=Color.red()))
					except Exception as e:
						print(e)

					return await status.edit(embed=discord.Embed(description=f'> {Emojis.APPROVE} **Locked** ticket.', color=Colors.BASE_COLOR), view=TicketModPanel())
					
		
			else:
				return await ctx.deny('This **ticket** is already **locked**.')
						
		else:	
			return await ctx.deny('This **channel** is not a **ticket**.')		

	@ticket.command(
			name='open', 
			description='Opens a ticket.', 
			aliases=['unlock', 'to', 'tu'], 
	)
	@guild_only()
	@cooldown(1,5, commands.BucketType.channel)
	async def open_ticket(self, ctx: StealContext) -> None:

		tpic = ctx.channel.topic
		if tpic:
			tpic1 = tpic.replace("Closed - ", "")
			tpic2 = tpic1.replace("Open - ", "")
		else:
			return await ctx.deny('This **channel** is not a **ticket** or the **topic** has been changed.')
		op = await ctx.guild.fetch_member(int(tpic2))

		if ctx.channel.topic and "Closed - " or "Open - " in ctx.channel.topic:
			if not op in ctx.channel.members or "Closed - " in tpic:
					status = await ctx.send(embed=discord.Embed(description=f'> {Emojis.WARN} **Opening** ticket. . .', color=Colors.WARN_COLOR))

					async for message in ctx.channel.history():
						if message.author.id == self.bot.user.id:
							if message.components:
								view = discord.ui.View.from_message(message)
								for child in view.children:
									child.disabled = True
								await message.edit(view=view)


					overwrites = {
					ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel = False),
					op: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=False),
					ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
					}

					await ctx.channel.edit(topic=f"Open - {op.id}", overwrites=overwrites,)

					try:
						await asyncio.wait_for(ctx.channel.edit(name=f"{op.name}"),timeout=2)
					except asyncio.TimeoutError:
						await ctx.channel.send(embed=discord.Embed(description=f"> {Emojis.WARN} Rate limited. Skipping channel name change.",color=Colors.WARN_COLOR))
					except Exception as e:
						print(e)

					await status.edit(embed=discord.Embed(description=f'> {Emojis.APPROVE} **Opened** ticket.', color=Colors.BASE_COLOR), view=TicketClose())
					return
		
			if op in ctx.channel.members:
				return await ctx.warn('This **ticket** is already **open**.')
				
		else:
			return await ctx.warn('This **channel** is not a **ticket**.')	

async def setup(bot):
	await bot.add_cog(Tickets(bot))