import humanfriendly

from discord.ext import commands
from discord.ext.commands import *
import discord
from managers.context import StealContext

import aiohttp
import datetime

from pydantic import BaseModel
from discord.ext import commands
from typing import Any, Optional
from isHex import isHex

from socials import socials


class ValidTime(commands.Converter):
    async def convert(self, ctx: StealContext, argument: str):
        try:
            time = humanfriendly.parse_timespan(argument)
        except humanfriendly.InvalidTimespan:
            raise commands.BadArgument(f"**{argument}** is an invalid timespan")

        return time
    
class ValidPunishment(commands.Converter):
    async def convert(self, ctx: StealContext, argument: str):
        punishments = ["ban", "mute", "kick"]
        
        if argument in punishments:
            return argument.lower()
        raise commands.BadArgument(f"**{argument}** is an invalid punishment.")
    
class ValidHex(commands.Converter):
    async def conver(self, ctx: StealContext, argument: str):
        if isHex(str.strip("#")):
            return str.strip("#")
        raise commands.BadArgument(f"**{argument}** is not a valid **hex** code")