import humanfriendly

from discord.ext import commands
from managers.context import StealContext

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