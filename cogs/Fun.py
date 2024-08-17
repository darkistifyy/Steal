import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
import python_weather as pw
from discord import *
import asyncio
import random
import aiohttp
import time
import orjson

from tools.Steal import Steal
from managers.context import StealContext

from typing import List, Optional, Union
from tools.Config import Colors, Emojis
from discord.ext import commands
import discord
import random

import aiohttp
import discord
from discord.ext import commands


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

	@command(
			name="ping",
			description="Bot ping.",
	)
	async def ping(self,ctx: StealContext) -> None:
		time_1 = time.perf_counter()
		await ctx.typing()
		time_2 = time.perf_counter()
		ping = round((time_2-time_1)*1000)

		out = await ctx.send(f"Websocket: **{ping}ms**")

		time_1 = time.perf_counter()
		await out.edit(content=f"Websocket: **{ping}ms** (edit: ``...ms``)")
		time_2 = time.perf_counter()
		ping2= round((time_2-time_1)*1000)

		await out.edit(content=f"Websocket: **{ping}ms** (edit: ``{ping2}ms``)")

	@command(
			name="tic",
			description="TTT battle with an opp.",
	)
	@guild_only()
	async def tic(self, ctx: StealContext, opp: discord.Member) -> None:

		await ctx.neutral(f"Tic Tac Toe, {ctx.author.mention} goes first.",view=TicTacToe())

		global player1
		global player2

		player1 = ctx.author
		player2 = opp

	@command(
			name="explode",
			description="Explodes a user.",
	)
	@guild_only()
	async def explode(self, ctx: StealContext, opp: discord.Member) -> None:		
		await ctx.warn(f"Are you sure you would like to explode {opp.mention}", view=Explosion())
		global explosionuser
		explosionuser = opp	

	@command(
		name="weather",
			description="Gets the forecast in the selected area.",
	)
	@cooldown(1,15, BucketType.guild)
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
	@cooldown(1,5, BucketType.user)
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

	@command(
			name="eightball",
			description="Ask the eightball a question.",
			aliases=["8ball", "eb"]
	)
	async def eightball(self, ctx: StealContext, *, question: str):
		
		await ctx.reply(
			embed=discord.Embed(
				title="__Magical eightball__",
				color=Colors.BASE_COLOR
			).add_field(
				name="Question:",
				value=f"{question.capitalize()}",
				inline=False
			).add_field(
				name="Answer:",
				value=f"{random.choice(['yes', 'no', 'never', 'most likely', 'absolutely', 'absolutely not', 'of course not']).capitalize()}",
				inline=False
			).set_author(
				name=ctx.author,
				icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
			)
		)

	@command(
			name="bird",
			description="Sends a random bird pic.",
			aliases=["birb"]
	)
	async def bird(self, ctx: StealContext):

		data = await self.bot.session.get_json("https://api.alexflipnote.dev/birb")
		await ctx.reply(
			file=File(fp=await self.bot.getbyte(data["file"]), filename="bird.png")
		)

	@command(
			name="dog",
			description="Sends a random dog pic.",
	)
	@cooldown(3,5, BucketType.user)
	async def dog(self, ctx: StealContext):

		data = await self.bot.session.get_json("https://random.dog/woof.json")
		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["url"]),
				filename=f"dog{data['url'][-4:]}",
			)
		)

	@command(
			name="cat",
			description="Sends a random cat pic.",
	)
	@cooldown(3,5, BucketType.user)
	async def cat(self, ctx: StealContext):

		data = (
			await self.bot.session.get_json(
				"https://api.thecatapi.com/v1/images/search"
			)
		)[0]
		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["url"]),
				filename="cat.png"
			)
		)

	@command(
			name="capybara",
			description="Sends a random capybara image.",
	)
	async def capybara(self, ctx: StealContext):

		data = await self.bot.session.get_json(
			"https://api.capy.lol/v1/capybara?json=true"
		)
		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["data"]["url"]),
				filename="capybara.png"
			)
		)

	@command(
			name="lizard",
			description="Sends a random lizard image.",
	)
	async def lizard(self, ctx: StealContext):

		data = await self.bot.session.get_json(
			"https://nekos.life/api/v2/img/lizard",
		)

		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["url"]),
				filename="lizard.png"
			)
		)


	@command(
			name="panda",
			description="Sends a random panda image.",
	)
	async def panda(self, ctx: StealContext):

		data = await self.bot.session.get_json(
			"https://some-random-api.ml/img/panda",
		)

		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["link"]),
				filename="panda.png"
			)
		)

	@command(
			name="fox",
			description="Sends a random fox image.",
			aliases=['floof']
	)
	async def fox(self, ctx: StealContext):

		data = await self.bot.session.get_json(
			"https://randomfox.ca/floof/",
		)

		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["image"]),
				filename="fox.png"
			)
		)

	@command(
			name="duck",
			description="Sends a random duckie image.",
			aliases=['quack', 'duckie']
	)
	async def duck(self, ctx: StealContext):

		data = await self.bot.session.get_json(
			"https://random-d.uk/api/v1/random?type=png",
		)

		await ctx.reply(
			file=File(
				fp=await self.bot.getbyte(data["url"]),
				filename="duck.png"
			)
		)

	@command(
			name='uselessfact',
			description='Sends a useless fact.',
			aliases=["fact", "uf"]
	)
	async def uselessfact(self, ctx: StealContext):

		data = (
			await self.bot.session.get_json(
				"https://uselessfacts.jsph.pl/random.json?language=en"
			)
		)["text"]
		await ctx.neutral(data)


	@command(
			name="choose",
			description="Picks between two choices.",
	)
	async def choose_cmd(self, ctx: StealContext, *, choices: str):
		choices1 = choices.split(", ")
		if len(choices1) == 1:
			return await ctx.warn("please put a `,` between your choices")

		final = random.choice(choices1)
		await ctx.neutral(f"I choose **{final}**")

	@command(
			name="ship",
			description="The ship \% between you and a member",
	)
	async def ship(self, ctx: StealContext, member: discord.Member):

		return await ctx.neutral(
			f"**{ctx.author.name}** 💞 **{member.name}** = **{random.randrange(101)}%**"
		)

	@command(
			name="advice",
			description="Sends random advice.",
	)
	async def advice(self, ctx: StealContext):

		data = orjson.loads(
			await self.bot.session.get_text("https://api.adviceslip.com/advice")
		)
		return await ctx.neutral(data["slip"]["advice"])


	@command(
			name="pack",
			description="Packs a member.",
			aliases=["flame"]
	)
	async def pack(self, ctx: StealContext, member: discord.Member):

		if member == ctx.author:
			return await ctx.warn("Why?")

		result = await self.bot.session.get_json(
			"https://evilinsult.com/generate_insult.php?lang=en&type=json"
		)
		await ctx.neutral(
			f"{member.mention} {result['insult']}",
		)


	@command(
		name="bitches",
		description="Shows the bitches of a member.",
		aliases=["bitchrate"],
	)
	async def bitches(self, ctx: StealContext, *, user: Optional[discord.Member] = Author):
		choices = ["regular", "still regular", "lol", "xd", "id", "zero", "infinite"]
		if random.choice(choices) == "infinite":
			result = "∞"
		elif random.choice(choices) == "zero":
			result = "0"
		else:
			result = random.randint(0, 100)
		await ctx.neutral(f"{user.mention} has **{result}** bitches")

	@command(
			name="gayrate",
			description="Shows the gay \% of a member.",
			aliases=["gay"]
	)
	async def gay(self, ctx: StealContext, *, member: Optional[discord.Member] = Author):

		return await ctx.neutral(f"{member.mention} is **{random.randint(0, 100)}%** gay 🏳️‍🌈")

	@command(
			name="ppsize",
			description="Shows the pp size of a member.",
			aliases=["pp"]
	)
	async def pp(self, ctx: StealContext, *, member: Optional[discord.Member] = Author):
	
		length = "===================="
		return await ctx.neutral(f"{member.mention}'s penis\n\n8{length[random.randint(1, 20):]}D")

	@command(
			name="kiss",
			description="Kisses a member.",
			aliases=["smooch"]
	)
	async def kiss(self, ctx: StealContext, member: discord.Member):

		if member == ctx.author:
			return await ctx.deny("Get help.")

		gif = await self.bot.session.get_json(
			"https://api.otakugifs.xyz/gif?reaction=kiss"
		)
		embed = Embed(
			color=Colors.BASE_COLOR,
			description=f"**{ctx.author.name}** kissed **{member.name}**",
		)
		embed.set_image(url=gif["url"])
		return await ctx.reply(embed=embed)

	@command(
			name="cuddle",
			description="Cuddles a member.",
			aliases=["snuggle"]
	)
	async def cuddle(self, ctx: StealContext, member: discord.Member):

		if member == ctx.author:
			return await ctx.deny("Get help.")

		gif = await self.bot.session.get_json(
			"https://api.otakugifs.xyz/gif?reaction=cuddle"
		)
		embed = Embed(
			color=Colors.BASE_COLOR,
			description=f"**{ctx.author.name}** cuddles **{member.name}**",
		).set_image(url=gif["url"])
		return await ctx.reply(embed=embed)

	@command(
			name="hug",
			description="Hugs a member.",
	)
	async def hug(self, ctx: StealContext, member: discord.Member):

		if member == ctx.author:
			return await ctx.deny("Get help.")

		gif = await self.bot.session.get_json(
			f"https://api.otakugifs.xyz/gif?reaction=hug"
		)
		embed = Embed(
			color=Colors.BASE_COLOR,
			description=f"**{ctx.author.name}** hugged **{member.name}**",
		).set_image(url=gif["url"])
		return await ctx.reply(embed=embed)

	@command(
			name="pat",
			description="Pats a member.",
			aliases=["pet"]
	)
	async def pat(self, ctx: StealContext, member: discord.Member):

		if member == ctx.author:
			return await ctx.deny("Get help.")

		gif = await self.bot.session.get_json(
			f"https://api.otakugifs.xyz/gif?reaction=pat"
		)
		embed = Embed(
			color=Colors.BASE_COLOR,
			description=f"**{ctx.author.name}** pats **{member.name}**",
		).set_image(url=gif["url"])
		return await ctx.reply(embed=embed)

	@command(
			name="slap",
			description="Slaps a member.",
			aliases=["smack"]
	)
	async def slap(self, ctx: StealContext, member: discord.Member):
	
		if member == ctx.author:
			return await ctx.deny("Get help.")

		gif = await self.bot.session.get_json(
			f"https://api.otakugifs.xyz/gif?reaction=slap"
		)
		embed = Embed(
			color=Colors.BASE_COLOR,
			description=f"**{ctx.author.name}** slaps **{member.name}**",
		).set_image(url=gif["url"])
		return await ctx.reply(embed=embed)

async def setup(bot):
	await bot.add_cog(Fun(bot))
