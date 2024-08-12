import discord
from discord import Color
from discord import ui
from discord.ui import Button,button, View
from discord.ext import commands
from discord.ext.commands import *
import python_weather as pw
from discord import *
import psutil
import asyncio
import sys
import random
import aiohttp
import time

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional
from tools.Config import Colors, Emojis
from discord.ext import commands
import discord

class Explosion(discord.ui.View):
	def __init__(self):
		super().__init__()

	global explosionuser
 
	@discord.ui.button(label='Confirm', emoji=f"{Emojis.APPROVE}", style=discord.ButtonStyle.green)
	async def confirm(self,interaction:discord.Interaction,button:discord.ui.Button):
		for button in self.children:
			button.disabled=True
		await interaction.message.edit(embed=discord.Embed(description=f"{Emojis.APPROVE} You have confirmed the explosion of {explosionuser.mention}.", color=Colors.BASE_COLOR),view=self)
		await interaction.response.defer()

		self.stop()
	@discord.ui.button(label="Cancel", emoji=f"{Emojis.DENY}", style=discord.ButtonStyle.danger)
	async def cancel(self,interaction:discord.Interaction,button:discord.ui.Button):
		for button in self.children:
			button.disabled=True
		await interaction.message.edit(embed=discord.Embed(description=f'{Emojis.DENY} You have cancelled the explosion of {explosionuser.mention}.', color=Colors.DENY_COLOR()),view=self)
		await interaction.response.defer()

		self.stop()

class TicTacToeButton(discord.ui.Button['TicTacToe']):
	def __init__(self, x: int, y: int):

		super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
		self.x = x
		self.y = y

	async def callback(self, interaction: discord.Interaction):

		global player1
		global player2
		EMESSGEE = interaction.message

		assert self.view is not None
		view: TicTacToe = self.view
		state = view.board[self.y][self.x]
		if state in (view.X, view.O):
			return

		if view.current_player == view.X:
			if interaction.user == player1:
				self.style = discord.ButtonStyle.danger
				self.label = 'X'
				self.disabled = True
				view.board[self.y][self.x] = view.X
				view.current_player = view.O
				desc=f"It is now {player2.mention}'s turn!"
			else:
				r1 = discord.Embed(description=f'{interaction.user.mention}, Please wait for your turn!', color=Color.red())
				r2 = discord.Embed(description=f'{interaction.user.mention}, You are not involved in this game.', color=Color.red())
				await interaction.response.send_message(embed=r1 if interaction.user==player2 else r2, ephemeral=True)
				return
		else:
			if interaction.user == player2:
				self.style = discord.ButtonStyle.success
				self.label = 'O'
				self.disabled = True
				view.board[self.y][self.x] = view.O
				view.current_player = view.X
				desc=f"It is now {player1.mention}'s turn!"
			else:
				r1 = discord.Embed(description=f'{interaction.user.mention}, Please wait for your turn!', color=Color.red())
				r2 = discord.Embed(description=f'{interaction.user.mention}, You are not involved in this game.', color=Color.red())
				await interaction.response.send_message(embed=r1 if interaction.user==player1 else r1, ephemeral=True)
				return

		winner = view.check_board_winner()
		if winner is not None:
			if winner == view.X:
				desc = f'{player1.mention} (X) won!'
			elif winner == view.O:
				desc = f'{player2.mention} (O) won!'
			else:
				desc = "It's a tie!"

			for child in view.children:
				child.disabled = True

			view.stop()

		await EMESSGEE.edit(embed=discord.Embed(description=desc, color=Color.pink()), view=view)
		await interaction.response.defer()
		



class TicTacToe(discord.ui.View):

	children: List[TicTacToeButton]
	X = -1
	O = 1
	Tie = 2

	def __init__(self):
		super().__init__()
		self.current_player = self.X
		self.board = [
			[0, 0, 0],
			[0, 0, 0],
			[0, 0, 0],
		]

		for x in range(3):
			for y in range(3):
				self.add_item(TicTacToeButton(x, y))

	def check_board_winner(self):
		for across in self.board:
			value = sum(across)
			if value == 3:
				return self.O
			elif value == -3:
				return self.X

		for line in range(3):
			value = self.board[0][line] + self.board[1][line] + self.board[2][line]
			if value == 3:
				return self.O
			elif value == -3:
				return self.X

		diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
		if diag == 3:
			return self.O
		elif diag == -3:
			return self.X

		diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
		if diag == 3:
			return self.O
		elif diag == -3:
			return self.X
		
		if all(i != 0 for row in self.board for i in row):
			return self.Tie

		return None


class Fun(commands.Cog):
	def __init__(self, bot:Steal):
		self.bot = bot
		self.MatchStart = {}
		self.lifes = {}

	@command(name="ping", description='Bot ping.')
	async def ping(self, ctx: StealContext) -> None:
		time_1 = time.perf_counter()
		await ctx.typing(1)
		time_2 = time.perf_counter()
		ping = round((time_2-time_1)*1000)
		await ctx.neutral(f"Latency (ms): `{ping}`")

	@command(name="tic", description="TTT battle with an opp.")
	@guild_only()
	async def tic(self, ctx: StealContext, opp: discord.Member) -> None:
		await ctx.neutral(f"Tic Tac Toe, {ctx.author.mention} goes first.",view=TicTacToe())

		global player1
		global player2

		player1 = ctx.author
		player2 = opp

	@command(name='explode', description='Explodes a user.')
	@guild_only()
	async def explode(self, ctx: StealContext, opp: discord.Member) -> None:
		await ctx.warn(f'Are you sure you would like to explode {opp.mention}', view=Explosion())
		global explosionuser
		explosionuser = opp	

	@command(name='weather', description='Gets the forecast in the selected area.')
	@cooldown(1,15, commands.BucketType.guild)
	async def weather(self, ctx: StealContext, *, location: str) -> None:

		msg = await ctx.send(embed=discord.Embed(description=f'{Emojis.WARN} Gathering Data...', color=Colors.WARN_COLOR))

		async with pw.Client(unit=pw.METRIC) as client:
			weather = await client.get(location)
			await msg.edit(embed=discord.Embed(title=f'{weather.description} in {location.capitalize()}',
			color=Colors.BASE_COLOR).add_field(
				name='Temperature', value=f'`{weather.temperature}C°`').add_field(
				name='Humidity', value=f'`{weather.humidity}%`').add_field(
				name='Wind Speed', value=f'`{weather.wind_speed} Km/h`').set_author(
				icon_url=ctx.author.avatar.url, name=ctx.author.name))	

	async def get_string(self): 
		lis = await self.get_words()
		word = random.choice(lis)
		return word[:3].lower()

	async def get_words(self): 
		async with aiohttp.ClientSession() as cs: 
			async with cs.get("https://www.mit.edu/~ecprice/wordlist.100000") as r: 
				byte = await r.read()
				data = str(byte, 'utf-8')
				return data.splitlines()

	@command(
		name = "blacktea",
		description = "Play a game of blacktea."
	)
	@cooldown(1, 5, commands.BucketType.user)
	@guild_only()
	async def blacktea(self, ctx: StealContext) -> None: 
		try:
			if self.MatchStart[ctx.guild.id] is True: 
				return await ctx.deny("Somebody in this server is already playing blacktea.", mention_author=False)
		except KeyError: 
			pass 

		self.MatchStart[ctx.guild.id] = True 
		embed = discord.Embed(color=Colors.BASE_COLOR, title="BlackTea Matchmaking", description=f"⏰ Waiting for players to join. To join react with 🍵.\nThe game will begin in **10 seconds**")
		embed.add_field(name="goal", value="You have **10 seconds** to say a word containing the given group of **3 letters.**\nIf failed to do so, you will lose a life. Each player has **2 lifes**")
		embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)  
		mes = await ctx.send(embed=embed)
		await mes.add_reaction("🍵")
		await asyncio.sleep(10)
		me = await ctx.channel.fetch_message(mes.id)
		players = [user.id async for user in me.reactions[0].users()]
		players.remove(self.bot.user.id)

		if len(players) < 2:
			self.MatchStart[ctx.guild.id] = False
			return await ctx.neutral(f"😦 {ctx.author.mention}, not enough players joined to start blacktea".format(ctx.author.mention), allowed_mentions=discord.AllowedMentions(users=True)) 

		while len(players) > 1: 
			for player in players: 
				strin = await self.get_string()
				await ctx.neutral(f"⏰ <@{player}>, type a word containing **{strin.upper()}** in **10 seconds**", allowed_mentions=discord.AllowedMentions(users=True))
			
				def is_correct(msg): 
					return msg.author.id == player
			
				try: 
					message = await self.bot.wait_for('message', timeout=10, check=is_correct)
				except asyncio.TimeoutError: 
					try: 
						self.lifes[player] = self.lifes[player] + 1  
						if self.lifes[player] == 3: 
							await ctx.neutral(f" <@{player}>, you're eliminated ☠️", allowed_mentions=discord.AllowedMentions(users=True))
							self.lifes[player] = 0
							players.remove(player)
							continue 
					except KeyError:  
						self.lifes[player] = 0   
					await ctx.neutral(f"💥 <@{player}>, you didn't reply on time! **{2-self.lifes[player]}** lifes remaining", allowed_mentions=discord.AllowedMentions(users=True))    
					continue
				if not strin.lower() in message.content.lower() or not message.content.lower() in await self.get_words():
					try: 
						self.lifes[player] = self.lifes[player] + 1  
						if self.lifes[player] == 3: 
							await ctx.send(f" <@{player}>, you're eliminated ☠️", allowed_mentions=discord.AllowedMentions(users=True))
							self.lifes[player] = 0
							players.remove(player)
							continue 
					except KeyError:  
						self.lifes[player] = 0 
					await ctx.neutral(f"💥 <@{player}>, incorrect word! **{2-self.lifes[player]}** lifes remaining", allowed_mentions=discord.AllowedMentions(users=True))
				else: 
					await message.add_reaction("✅")  
			
		await ctx.neutral(f"👑 <@{players[0]}> won the game!", allowed_mentions=discord.AllowedMentions(users=True))
		self.lifes[players[0]] = 0
		self.MatchStart[ctx.guild.id] = False   

async def setup(bot):
	await bot.add_cog(Fun(bot))