import asqlite
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from dotenv import *

from tools.EmbedBuilder import EmbedBuilder, EmbedScript
from tools.EmbedBuilderUi import Embed, EmbedEditor
from tools.Steal import Steal


class Members(commands.Cog):
    def __init__(self, bot: Steal):
        self.bot = bot

    @Cog.listener("on_member_join")
    async def on_join_autorole_event(self, member: discord.Member) -> None:
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS autorole(guildid INTEGER, roleid INTEGER)"
                )

                cur = await cursor.execute(
                    """
					SELECT * FROM autorole WHERE guildid = $1
					""",
                    member.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    if row[1]:
                        try:
                            role = member.guild.get_role(row[1])
                        except:
                            return
                        if role is not None:
                            await member.add_roles(role, reason="Autorole Add")

    @Cog.listener("on_member_join")
    async def on_join_welcome_event(self, member: discord.Member) -> None:
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS welcome(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
                )

                cur = await cursor.execute(
                    """
					SELECT * FROM welcome WHERE guildid = $1
					""",
                    member.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    toggle = row[2]
                    if toggle == 1:
                        channelid = row[1]
                        try:
                            channel = self.bot.get_channel(channelid)
                        except:
                            return

                        parsed = EmbedBuilder.embed_replacement(member, row[3])
                        content, embed, view = await EmbedBuilder.to_object(parsed)

                        if channel:
                            await channel.send(content=content, embed=embed, view=None)

    @Cog.listener("on_member_update")
    async def on_boost_event(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:

                def check(before, after):
                    if not before.guild.premium_subscriber_role:
                        if after.guild.premium_subscriber_role:
                            return True
                    return False

                if not check(before, after):
                    return

                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS boostresponse(guildid INTEGER, channelid INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), script TEXT)"
                )

                cur = await cursor.execute(
                    """
					SELECT * FROM boostresponse WHERE guildid = $1
					""",
                    before.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    toggle = row[2]
                    if toggle == 1:
                        channelid = row[1]
                        try:
                            channel = self.bot.get_channel(channelid)
                        except:
                            return

                        parsed = EmbedBuilder.embed_replacement(after, row[3])
                        content, embed, view = await EmbedBuilder.to_object(parsed)

                        if channel:
                            await channel.send(content=content, embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(Members(bot))
