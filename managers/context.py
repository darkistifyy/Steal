import discord

from typing import List, Union

from discord import Message, Embed
from discord.ext.commands import Context, Group

from tools.Config import Colors, Emojis
from tools.Paginator import Paginator
from discord import utils

class StealContext(Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def approve(self, message: str, **kwargs) -> Message:
        embed=discord.Embed(
            color = Colors.APPROVE_COLOR,
            description = f'> {Emojis.APPROVE} {self.author.mention}: {message}'
        )
        await self.reply(
            embed=embed,
            **kwargs,
        )

    async def warn(self, message: str, **kwargs) -> Message:
        embed=discord.Embed(
            color = Colors.WARN_COLOR,
            description = f'> {Emojis.WARN} {self.author.mention}: {message}'
        )
        await self.reply(
            embed=embed,
            **kwargs,
        )
    
    async def deny(self, message: str, **kwargs) -> Message:
        embed=discord.Embed(
            color = Colors.DENY_COLOR,
            description = f'> {Emojis.DENY} {self.author.mention}: {message}'
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def neutral(self, message: str, **kwargs) -> Message:
        embed=discord.Embed(
            color = Colors.NEUTRAL_COLOR,
            description = f'> {self.author.mention}: {message}'
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def msg(self, message: str, **kwargs) -> Message:
        embed=discord.Embed(
            color = Colors.BASE_COLOR,
            description = f'> {message}'
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def music(self, message: str, **kwargs) -> Message:
        embed=discord.Embed(
            color = Colors.BASE_COLOR,
            description = f'> {Emojis.MUSIC} {self.author.mention}: {message}'
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def plshelp(self):
        return await self.send_help(self.command)

    async def paginate(self, embeds: List[discord.Embed], **kwargs) -> Message:

        view  = Paginator(self, embeds)

        if len(embeds) > 1:

            out = await self.reply(
                embed = embeds[0],
                view  = view,
                **kwargs
            )

        else:
            out = await self.reply(
                embed = embeds[0],
                view  = None,
                **kwargs
            )

        view.response = out




