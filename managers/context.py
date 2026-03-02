from typing import List

import discord
from discord import Message
from discord.ext.commands import Context, Group

from tools.Config import Colors, Emojis, Guild
from tools.Paginator import Paginator


class StealContext(Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def approve(self, message: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.APPROVE_COLOR,
            description=f"> {Emojis.APPROVE} {self.author.mention} {message}",
        )
        await self.reply(
            embed=embed,
            **kwargs,
        )

    async def warn(self, message: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.WARN_COLOR,
            description=f"> {Emojis.WARN} {self.author.mention} {message}",
        )
        await self.reply(
            embed=embed,
            **kwargs,
        )

    async def deny(self, message: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.DENY_COLOR,
            description=f"> {Emojis.DENY} {self.author.mention} {message}",
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def exception(self, code: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.WARN_COLOR,
            description=f"> {Emojis.WARN} {self.author.mention} Exception caught in the error code above. Join the [**Support Server**]({Guild.INVITE}) for assistance.",
        )
        return await self.reply(
            content=f"`{str(code)}`",
            embed=embed,
            **kwargs,
        )

    async def image(self, url: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.BASE_COLOR,
        )
        embed.set_image(url=url)

        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def neutral(self, message: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.NEUTRAL_COLOR,
            description=f"> {self.author.mention}: {message}",
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def msg(self, message: str, **kwargs) -> Message:
        embed = discord.Embed(color=Colors.BASE_COLOR, description=f"> {message}")
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def music(self, message: str, **kwargs) -> Message:
        embed = discord.Embed(
            color=Colors.BASE_COLOR,
            description=f"> {Emojis.MUSIC} {self.author.mention} {message}",
        )
        return await self.reply(
            embed=embed,
            **kwargs,
        )

    async def plshelp(self):
        return await self.send_help(self.command)

    async def paginate(self, embeds: List[discord.Embed], **kwargs) -> Message:

        view = Paginator(self, embeds)

        if len(embeds) > 1:
            out = await self.reply(embed=embeds[0], view=view, **kwargs)

        else:
            out = await self.reply(embed=embeds[0], view=None, **kwargs)

        view.response = out
