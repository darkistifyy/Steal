import datetime

import asqlite
import discord
import humanfriendly
import humanize
from discord.ext import commands
from discord.ext.commands import *
from dotenv import *

from tools.Config import Colors, Emojis
from tools.Steal import Steal

url_prefixes = (
    "discord.com/invite/",
    "discord.gg/",
    "gg/",
)


class Messages(commands.Cog):
    def __init__(self, bot: Steal):
        self.bot = bot
        self.afkstatus = False
        self.invitestatus = False

    @Cog.listener("on_message")
    async def filter_message_invite_event(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.is_system():
            return
        if not message.author:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
					CREATE TABLE IF NOT EXISTS invitesautomod(guildid INTEGER, punishment TEXT, duration INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)))
					""",
                )

                cur = await cursor.execute(
                    """
					SELECT * FROM invitesautomod WHERE guildid = $1
					""",
                    message.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    if row[3] == 1:
                        for prefix in url_prefixes:
                            if prefix in message.content:
                                split1 = message.content.split(prefix)[1]
                                code = split1.split(" ")[0]

                                try:
                                    invite = await self.bot.fetch_invite(code)
                                except:
                                    return

                                if invite:
                                    if invite.guild.id != message.guild.id:
                                        try:
                                            embed = (
                                                discord.Embed(
                                                    description=f"> {Emojis.WARN} {message.author.mention}: Your message in **{message.guild.name}** was flagged for containing an **invite**.",
                                                    color=Colors.WARN_COLOR,
                                                )
                                                .add_field(
                                                    name="Your message",
                                                    value=f"`{message.content}`",
                                                    inline=True,
                                                )
                                                .add_field(
                                                    name="Flagged invite",
                                                    value=f"`{code}`",
                                                    inline=True,
                                                )
                                                .set_author(
                                                    name=message.guild.name,
                                                    icon_url=message.guild.icon.url
                                                    if message.guild.icon
                                                    else "https://none.none",
                                                )
                                            )

                                            if row[1].lower() != "none":
                                                embed.add_field(
                                                    name="Punishment",
                                                    value=f"`{row[1].capitalize()} - {humanfriendly.format_timespan(row[2]) if row[2] > 0 else ''}`",
                                                    inline=True,
                                                )

                                            await message.author.send(embed=embed)

                                        except Exception as e:
                                            print(e)

                                        if row[1].lower() != "none":
                                            if row[1].lower() == "ban":
                                                try:
                                                    await message.guild.ban(
                                                        message.author,
                                                        reason=f"AUTOMOD | Sent invite, code: {code}",
                                                    )
                                                except:
                                                    pass
                                            if row[1].lower() == "kick":
                                                try:
                                                    await message.guild.kick(
                                                        message.author,
                                                        reason=f"AUTOMOD | Sent invite, code: {code}",
                                                    )
                                                except:
                                                    pass
                                            if row[1].lower() == "mute":
                                                try:
                                                    await message.author.timeout(
                                                        discord.utils.utcnow()
                                                        + datetime.timedelta(
                                                            seconds=row[2]
                                                        ),
                                                        reason=f"AUTOMOD | Sent invite, code: {code}",
                                                    )
                                                except Exception as e:
                                                    print(e)
                                        return

    @Cog.listener("on_message")
    async def filter_message_blacklist_event(self, message: discord.Message):
        if message.author.bot:
            return
        if message.is_system():
            return
        if not message.author:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER UNIQUE, punishment TEXT, duration INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words TEXT)",
                )

                cur = await cursor.execute(
                    """
					SELECT * FROM wordsautomod WHERE guildid = $1
					""",
                    message.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    if row[3] == 1:
                        if message.content.startswith(
                            f"{self.bot.command_prefix}filter words remove"
                        ) or message.content.startswith(
                            f"{self.bot.command_prefix}filter words add"
                        ):
                            if message.author.guild_permissions.manage_messages:
                                return

                        things = [word for word in row[4].split(",") if word]

                        for thing in things:
                            if thing.lower() in message.content.lower():
                                try:
                                    embed = (
                                        discord.Embed(
                                            description=f"> {Emojis.WARN} {message.author.mention}: Your message in **{message.guild.name}** was flagged for containing a blocked **phrase**.",
                                            color=Colors.WARN_COLOR,
                                        )
                                        .add_field(
                                            name="Your message",
                                            value=f"`{message.content}`",
                                            inline=True,
                                        )
                                        .add_field(
                                            name="Flagged phrase",
                                            value=f"`{thing}`",
                                            inline=True,
                                        )
                                    )
                                    if row[1].lower() != "none":
                                        embed.add_field(
                                            name="Punishment",
                                            value=f"`{row[1].capitalize()} - {humanfriendly.format_timespan(row[2]) if row[2] > 0 else ''}`",
                                            inline=True,
                                        )
                                    await message.author.send(embed=embed)

                                except:
                                    pass

                                if row[1].lower() != "none":
                                    if row[1].lower() == "ban":
                                        try:
                                            if not message.author.guild_permissions.ban_members:
                                                await message.guild.ban(
                                                    message.author,
                                                    reason=f"AUTOMOD | Flagged phrase, code: {thing}",
                                                )
                                        except:
                                            pass
                                    if row[1].lower() == "kick":
                                        try:
                                            if not message.author.guild_permissions.kick_members:
                                                await message.guild.kick(
                                                    message.author,
                                                    reason=f"AUTOMOD | Flagged phrase, code: {thing}",
                                                )
                                        except:
                                            pass
                                    if row[1].lower() == "mute":
                                        try:
                                            if not message.author.guild_permissions.mute_members:
                                                await message.author.timeout(
                                                    discord.utils.utcnow()
                                                    + datetime.timedelta(
                                                        seconds=row[2]
                                                    ),
                                                    reason=f"AUTOMOD | Flagged phrase, code: {thing}",
                                                )
                                        except Exception as e:
                                            print(e)

                                return await message.delete()

    @Cog.listener("on_message_edit")
    async def filter_edit_blacklist_event(
        self, _: discord.Message, message: discord.Message
    ):
        if message.author.bot:
            return
        if message.is_system():
            return
        if not message.author:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS wordsautomod(guildid INTEGER UNIQUE, punishment TEXT, duration INTEGER, toggle BOOLEAN NOT NULL CHECK (toggle IN (0, 1)), words TEXT)",
                )

                cur = await cursor.execute(
                    """
					SELECT * FROM wordsautomod WHERE guildid = $1
					""",
                    message.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    if row[3] == 1:
                        if message.content.startswith(
                            f"{self.bot.command_prefix}filter words remove"
                        ) or message.content.startswith(
                            f"{self.bot.command_prefix}filter words add"
                        ):
                            if message.author.guild_permissions.manage_messages:
                                return

                        things = [word for word in row[4].split(",") if word]

                        for thing in things:
                            if thing.lower() in message.content.lower():
                                try:
                                    embed = (
                                        discord.Embed(
                                            description=f"> {Emojis.WARN} {message.author.mention}: Your message in **{message.guild.name}** was flagged for containing a blocked **phrase**.",
                                            color=Colors.WARN_COLOR,
                                        )
                                        .add_field(
                                            name="Your message",
                                            value=f"`{message.content}`",
                                            inline=True,
                                        )
                                        .add_field(
                                            name="Flagged phrase",
                                            value=f"`{thing}`",
                                            inline=True,
                                        )
                                    )
                                    if row[1].lower() != "none":
                                        embed.add_field(
                                            name="Punishment",
                                            value=f"`{row[1].capitalize()} - {humanfriendly.format_timespan(row[2]) if row[2] > 0 else ''}`",
                                            inline=True,
                                        )
                                    await message.author.send(embed=embed)

                                except:
                                    pass

                                if row[1].lower() != "none":
                                    if row[1].lower() == "ban":
                                        try:
                                            if not message.author.guild_permissions.ban_members:
                                                await message.guild.ban(
                                                    message.author,
                                                    reason=f"AUTOMOD | Flagged phrase, code: {thing}",
                                                )
                                        except:
                                            pass
                                    if row[1].lower() == "kick":
                                        try:
                                            if not message.author.guild_permissions.kick_members:
                                                await message.guild.kick(
                                                    message.author,
                                                    reason=f"AUTOMOD | Flagged phrase, code: {thing}",
                                                )
                                        except:
                                            pass
                                    if row[1].lower() == "mute":
                                        try:
                                            if not message.author.guild_permissions.mute_members:
                                                await message.author.timeout(
                                                    discord.utils.utcnow()
                                                    + datetime.timedelta(
                                                        seconds=row[2]
                                                    ),
                                                    reason=f"AUTOMOD | Flagged phrase, code: {thing}",
                                                )
                                        except Exception as e:
                                            print(e)

                                return await message.delete()

    @Cog.listener("on_message")
    async def afk_message_event(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.is_system():
            return
        if not message.author:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        if message.content.startswith(f"{self.bot.command_prefix}afk"):
            return
        if self.afkstatus == message.author:
            return
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS afk(guildid INTEGER, userid, status, time)"
                )

                cur = await cursor.execute(
                    "SELECT * FROM afk WHERE guildid = $1 AND userid = $2",
                    message.guild.id,
                    message.author.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    self.afkstatus = True
                    await cursor.execute(
                        "DELETE FROM afk WHERE guildid = $1 AND userid = $2",
                        message.guild.id,
                        row[1],
                    )

                    time = discord.utils.format_dt(
                        datetime.datetime.fromtimestamp(row[3]), style="R"
                    )

                    await message.reply(
                        embed=discord.Embed(
                            description=f"Welcome back {message.author.mention}! You dissappeared **{time}**",
                            color=Colors.BASE_COLOR,
                        )
                    )
                self.afkstatus = False

    @Cog.listener("on_message")
    async def afk_user_mention_event(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.is_system():
            return
        if not message.author:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS afk(guildid INTEGER, userid INTEGER, status TEXT, time INTEGER)"
                )

                cur = await cursor.execute(
                    "SELECT * FROM afk WHERE guildid = $1 AND userid = $2",
                    message.guild.id,
                    message.author.id,
                )

                row = await cur.fetchall()

                if row:
                    row = row[0]
                    if row[1]:
                        user = self.bot.get_user(row[1])
                        if user.mentioned_in(message):
                            status = row[2]
                            time = discord.utils.format_dt(
                                datetime.datetime.fromtimestamp(row[3]), style="R"
                            )
                            await message.reply(
                                embed=discord.Embed(
                                    description=f"> {user.mention} is AFK, **{status if status else 'Unretriveable status'}** - {time}",
                                    color=Colors.BASE_COLOR,
                                )
                            )

    @Cog.listener("on_message_delete")
    async def delete_message_log(self, message: discord.Message):
        if message.author.bot:
            return
        async with asqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS msglogs(guildid INTEGER, channelid)"
                )

                cur = await cursor.execute(
                    "SELECT * FROM msglogs WHERE guildid = $1",
                    message.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    channel = message.guild.get_channel(row[1])
                    if channel:
                        try:
                            await channel.send(
                                embed=discord.Embed(
                                    color=Colors.BASE_COLOR,
                                )
                                .add_field(
                                    name="Deleted message",
                                    value=f"> A **message** from {message.author.mention} (`{message.author}`) was **deleted** in {message.channel.mention}",
                                )
                                .add_field(
                                    name="Message content",
                                    value=f">>> {message.content}",
                                    inline=False,
                                )
                                .set_author(
                                    name=message.author,
                                    icon_url=message.author.display_avatar.url,
                                )
                            )
                        except:
                            pass

    @Cog.listener("on_message_edit")
    async def edit_message_log(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if before.author.bot:
            return
        async with asqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                cur = await cursor.execute(
                    "SELECT * FROM msglogs WHERE guildid = $1",
                    before.guild.id,
                )

                row = await cur.fetchone()
                await cursor.close()

                if row:
                    channel = before.guild.get_channel(row[1])
                    if channel:
                        try:
                            await channel.send(
                                embed=discord.Embed(
                                    color=Colors.BASE_COLOR,
                                )
                                .add_field(
                                    name="Edited message",
                                    value=f"{before.author.mention} (`{before.author}`) **edited** a message in {before.channel.mention}\n{f'> [**Jump Here**]({after.jump_url})' if after else ''}",
                                )
                                .add_field(
                                    name="Before",
                                    value=f">>> {before.content}",
                                    inline=False,
                                )
                                .add_field(
                                    name="After",
                                    value=f">>> {after.content}",
                                    inline=False,
                                )
                                .set_author(
                                    name=before.author,
                                    icon_url=before.author.display_avatar.url,
                                )
                            )
                        except:
                            pass

    @Cog.listener("on_message_delete")
    async def delete_snipe(self, message: discord.Message):
        if message.author.bot:
            return

        get_snipes = self.bot.cache.get("snipe")
        payload = [
            {
                "channel": message.channel.id,
                "name": str(message.author),
                "avatar": message.author.display_avatar.url,
                "message": message.content,
                "attachments": message.attachments,
                "stickers": message.stickers,
                "created_at": message.created_at.timestamp(),
            }
        ]

        if get_snipes:
            temp = self.bot.cache.get("snipe")
            temp.append(
                {
                    "channel": message.channel.id,
                    "name": str(message.author),
                    "avatar": message.author.display_avatar.url,
                    "message": message.content,
                    "attachments": message.attachments,
                    "stickers": message.stickers,
                    "created_at": message.created_at.timestamp(),
                }
            )
            return await self.bot.cache.set("snipe", temp)
        else:
            await self.bot.cache.set("snipe", payload)

    @Cog.listener("on_message_edit")
    async def edit_snipe(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if before.content == after.content:
            return

        edit_snipes = self.bot.cache.get("edit_snipe")
        if edit_snipes:
            edit_snipes.append(
                {
                    "channel": before.channel.id,
                    "name": str(before.author),
                    "avatar": before.author.display_avatar.url,
                    "before": before.content,
                    "after": after.content,
                    "edited_at": after.created_at.timestamp(),
                }
            )
            return await self.bot.cache.set("edit_snipe", edit_snipes)
        else:
            payload = [
                {
                    "channel": before.channel.id,
                    "name": str(before.author),
                    "avatar": before.author.display_avatar.url,
                    "before": before.content,
                    "after": after.content,
                    "edited_at": after.created_at.timestamp(),
                }
            ]
            return await self.bot.cache.set("edit_snipe", payload)

    @Cog.listener("on_reaction_remove")
    async def reaction_snipe_event(
        self, reaction: discord.Reaction, user: discord.Member
    ):

        if user.bot:
            return

        reaction_snipe = self.bot.cache.get("reaction_snipe")
        if reaction_snipe:
            reaction_snipe.append(
                {
                    "channel": reaction.message.channel.id,
                    "name": str(user),
                    "avatar": user.display_avatar.url,
                    "message": reaction.message.id,
                    "reaction": str(reaction.emoji),
                    "removed_at": datetime.datetime.now().timestamp(),
                }
            )
            await self.bot.cache.set("reaction_snipe", reaction_snipe)
        else:
            payload = [
                {
                    "channel": reaction.message.channel.id,
                    "name": str(user),
                    "avatar": user.display_avatar.url,
                    "message": reaction.message.id,
                    "reaction": str(reaction.emoji),
                    "removed_at": datetime.datetime.now().timestamp(),
                }
            ]
            await self.bot.cache.set("reaction_snipe", payload)


async def setup(bot):
    await bot.add_cog(Messages(bot))
