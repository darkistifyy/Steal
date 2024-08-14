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
        embed=Embed(
            color = Colors.BASE_COLOR,
            description = f'{Emojis.APPROVE} {self.author.mention}: {message}'
        )
        await self.reply(
            embed=embed,
            **kwargs
        )

    async def warn(self, message: str, **kwargs) -> Message:
            embed=Embed(
                color = Colors.WARN_COLOR,
                description = f'{Emojis.WARN} {self.author.mention}: {message}'
            )
            await self.reply(
                embed=embed,
                **kwargs
            )
    
    async def deny(self, message: str, **kwargs) -> Message:
        return await self.reply(
            embed=Embed(
                color = Colors.DENY_COLOR,
                description = f'{Emojis.DENY} {self.author.mention}: {message}'
            ),
            **kwargs
        )

    async def neutral(self, message: str, **kwargs) -> Message:
        return await self.reply(
            embed=Embed(
                color = Colors.NEUTRAL_COLOR,
                description = f'{message}'
            ),
            **kwargs
        )

    async def paginate(self, embeds: List[discord.Embed], **kwargs) -> Message:

        view  = Paginator(self, embeds)

        out = await self.reply(
            embed = embeds[0],
            view  = view,
            **kwargs
        )
        
        view.response = out