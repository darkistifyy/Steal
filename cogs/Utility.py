from __future__ import print_function, annotations

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import *
from discord.ui import *
from sklearn import *
import aiohttp
import io
import os
import zlib
import asqlite
import math
import datetime
import sys
from isHex import isHex
from tools.Validators import ValidTime
import humanfriendly
import humanize
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from tools.Steal import Steal
from tools.rtfm import fuzzy
from tools.EmbedBuilder import EmbedBuilder, EmbedScript
from managers.context import StealContext

import typing
from tools.Config import Colors, Emojis
from tools.View import UrlView

from typing import Optional

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}

from tools.bytesio import dom_color, caption_image, compress_image
import re
from typing import Generator, Union, Optional

from tools.EmbedBuilderUi import EmbedEditor, Embed

RTFM_PAGE_TYPES = {
    'stable': 'https://discordpy.readthedocs.io/en/stable',
    'stable-jp': 'https://discordpy.readthedocs.io/ja/stable',
    'latest': 'https://discordpy.readthedocs.io/en/latest',
    'latest-jp': 'https://discordpy.readthedocs.io/ja/latest',
    'python': 'https://docs.python.org/3',
    'python-jp': 'https://docs.python.org/ja/3',
}


try:
    from utils.ignored import HORRIBLE_HELP_EMBED  # type: ignore
except ImportError:
    HORRIBLE_HELP_EMBED = discord.Embed(description=f'{Emojis.WARN} No information avaliable....', color=Colors.WARN_COLOR)


__all__ = ('EmbedMaker', 'EmbedFlags')


def strip_codeblock(content: str) -> str:
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return content.strip('```')

    # remove `foo`
    return content.strip('` \n')


def verify_link(argument: str) -> str:
    link = re.fullmatch('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|%[0-9a-fA-F][0-9a-fA-F])+', argument)
    if not link:
        raise commands.BadArgument('Invalid URL provided.')
    return link.string

class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer: bytes):
        self.stream = io.BytesIO(buffer)

    def readline(self) -> str:
        return self.stream.readline().decode('utf-8')

    def skipline(self) -> None:
        self.stream.readline()

    def read_compressed_chunks(self) -> Generator[bytes, None, None]:
            decompressor = zlib.decompressobj()
            while True:
                chunk = self.stream.read(self.BUFSIZE)
                if len(chunk) == 0:
                    break
                yield decompressor.decompress(chunk)
            yield decompressor.flush()

    def read_compressed_lines(self) -> Generator[str, None, None]:
            buf = b''
            for chunk in self.read_compressed_chunks():
                buf += chunk
                pos = buf.find(b'\n')
                while pos != -1:
                    yield buf[:pos].decode('utf-8')
                    buf = buf[pos + 1 :]
                    pos = buf.find(b'\n')


class FieldFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    name: str
    value: str
    inline: bool = True


class FooterFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    text: str
    icon: typing.Annotated[str, verify_link] | None = None


class AuthorFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    name: str
    icon: typing.Annotated[str, verify_link] | None = None
    url: typing.Annotated[str, verify_link] | None = None


class EmbedFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    title: str | None = None
    description: str | None = None
    color: discord.Color | None = None
    field: typing.List[FieldFlags] = commands.flag(converter=list[FieldFlags], default=None)
    footer: FooterFlags | None = None
    image: typing.Annotated[str, verify_link] | None = None
    author: AuthorFlags | None = None
    thumbnail: typing.Annotated[str, verify_link] | None = None

    @classmethod
    async def convert(cls, ctx: StealContext, argument: str):  # pyright: ignore[reportIncompatibleMethodOverride]
        argument = strip_codeblock(argument).replace(' —', ' --')
        # Here we strip the code block if any and replace the iOS dash with
        # a regular double-dash for ease of use.
        return await super().convert(ctx, argument)


class JsonFlag(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    json: str


class EmbedMaker(commands.Cog):
    @commands.command()
    async def embed(
        self,
        ctx: StealContext,
        *,
        flags: typing.Union[typing.Literal['--help'], EmbedFlags, None],
    ):
        """Sends an embed using flags. An interactive embed maker is also available if you don't pass any flags.

        Parameters
        ----------
        flags: EmbedFlags
            The flags to use. Please see ``embed --help`` for flag info.
        """
        if flags is None:
            view = EmbedEditor(ctx.author, self)  # type: ignore

            if ctx.reference and ctx.reference.embeds:
                view.embed = Embed.from_dict(ctx.reference.embeds[0].to_dict())
                await view.update_buttons()
            view.message = await ctx.reply(embed=view.current_embed, view=view)
            return

        if flags == '--help':
            return await ctx.reply(embed=HORRIBLE_HELP_EMBED)

        embed = discord.Embed(title=flags.title, description=flags.description, colour=flags.color)

        if flags.field and len(flags.field) > 25:
            raise commands.BadArgument('You can only have up to 25 fields!')

        for f in flags.field or []:
            embed.add_field(name=f.name, value=f.value, inline=f.inline)

        if flags.thumbnail:
            embed.set_thumbnail(url=flags.thumbnail)

        if flags.image:
            embed.set_image(url=flags.image)

        if flags.author:
            embed.set_author(name=flags.author.name, url=flags.author.url, icon_url=flags.author.icon)

        if flags.footer:
            embed.set_footer(text=flags.footer.text, icon_url=flags.footer.icon or None)

        if not embed:
            raise commands.BadArgument('You must pass at least one of the necessary (marked with `*`) flags!')
        if len(embed) > 6000:
            raise commands.BadArgument('The embed is too big! (too much text!) Max length is 6000 characters.')
        if not flags.save:
            try:
                await ctx.channel.send(embed=embed)
            except discord.HTTPException as e:
                raise commands.BadArgument(f'Failed to send the embed! {type(e).__name__}: {e.text}`')
            except Exception as e:
                raise commands.BadArgument(f'An unexpected error occurred: {type(e).__name__}: {e}')

import re
import typing

import discord
from discord.ext import commands

from managers.interaction import PatchedInteraction
from managers.context import StealContext

from tools.EmbedBuilderUi import EmbedEditor, Embed

__all__ = ('EmbedMaker', 'EmbedFlags')


def strip_codeblock(content: str) -> str:
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return content.strip('```')

    # remove `foo`
    return content.strip('` \n')


def verify_link(argument: str) -> str:
    link = re.fullmatch('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|%[0-9a-fA-F][0-9a-fA-F])+', argument)
    if not link:
        raise commands.BadArgument('Invalid URL provided.')
    return link.string


class FieldFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    name: str
    value: str
    inline: bool = True


class FooterFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    text: str
    icon: typing.Annotated[str, verify_link] | None = None


class AuthorFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    name: str
    icon: typing.Annotated[str, verify_link] | None = None
    url: typing.Annotated[str, verify_link] | None = None


class EmbedFlags(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    title: str | None = None
    description: str | None = None
    color: discord.Color | None = None
    field: typing.List[FieldFlags] = commands.flag(converter=list[FieldFlags], default=None)
    footer: FooterFlags | None = None
    image: typing.Annotated[str, verify_link] | None = None
    author: AuthorFlags | None = None
    thumbnail: typing.Annotated[str, verify_link] | None = None

    @classmethod
    async def convert(cls, ctx: StealContext, argument: str):  # pyright: ignore[reportIncompatibleMethodOverride]
        argument = strip_codeblock(argument).replace(' —', ' --')
        # Here we strip the code block if any and replace the iOS dash with
        # a regular double-dash for ease of use.
        return await super().convert(ctx, argument)


class JsonFlag(commands.FlagConverter, prefix='--', delimiter='', case_insensitive=True):
    json: str

class ChannelDeleteConfirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Confirm", emoji="✅", style=discord.ButtonStyle.green, custom_id="channeldeleteconfirm")
    async def channeldeleteconfirm(self,interaction:discord.Interaction, button:Button):
        await interaction.response.defer()
        for button in self.children:
            button.disabled=True
            await interaction.message.edit(view=self)

        await interaction.channel.delete(
            reason=f'Executed by {interaction.user}'
        )
    @button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, custom_id="channeldeletecancel")
    async def channeldeletecancel(self, interaction:discord.Interaction, button:Button):
        await interaction.response.defer()
        for button in self.children:
            button.disabled=True
            return await interaction.message.edit(embed=discord.Embed(description=f"{Emojis.DENY} You have cancelled the deletion of {interaction.channel.mention}", color=Colors.DENY_COLOR), view=self)

class Utility(commands.Cog):
    def __init__(self, bot: Steal):
        self.bot = bot
        self.description = "Random utility commands lol."

    def parse_object_inv(self, stream: SphinxObjectFileReader, url: str) -> dict[str, str]:
        # key: URL
        # n.b.: key doesn't have `discord` or `discord.ext.commands` namespaces
        result: dict[str, str] = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != '# Sphinx inventory version 2':
            raise RuntimeError('Invalid objects.inv file version.')

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if 'zlib' not in line:
            raise RuntimeError('Invalid objects.inv file, not z-lib compatible.')

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(':')
            if directive == 'py:module' and name in result:
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue

            # Most documentation pages have a label
            if directive == 'std:doc':
                subdirective = 'label'

            if location.endswith('$'):
                location = location[:-1] + name

            key = name if dispname == '-' else dispname
            prefix = f'{subdirective}:' if domain == 'std' else ''

            if projname == 'discord.py':
                key = key.replace('discord.ext.commands.', '').replace('discord.', '')

            result[f'{prefix}{key}'] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self):
        cache: dict[str, dict[str, str]] = {}
        for key, page in RTFM_PAGE_TYPES.items():
            cache[key] = {}
            session = aiohttp.ClientSession()
            async with session.get(page + '/objects.inv') as resp:
                if resp.status != 200:
                    raise RuntimeError('Cannot build rtfm lookup table, try again later.')

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)
                await session.close()

        self._rtfm_cache = cache

    async def do_rtfm(self, ctx: StealContext, key: str, obj: str = commands.param(default=None, displayed_default=None) ):
        if obj is None:
            view = UrlView(RTFM_PAGE_TYPES[key], "Docs")
            out = await ctx.reply(
                    embed=discord.Embed(
                        title="Discord.py Docs",
                        description=f"Check the Discord.py docs [with the button below]({RTFM_PAGE_TYPES[key]})!",
                        color=Colors.BASE_COLOR
                    ).set_author(
                        name=ctx.author,
                        icon_url=ctx.author.display_avatar
                    ),view=view
            )
            view.message = out
            return

        if not hasattr(self, '_rtfm_cache'):
            await ctx.typing()
            await self.build_rtfm_lookup_table()

        obj = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)

        if key.startswith('latest'):
            # point the abc.Messageable types properly:
            q = obj.lower()
            for name in dir(discord.abc.Messageable):
                if name[0] == '_':
                    continue
                if q == name:
                    obj = f'abc.Messageable.{name}'
                    break

        cache = list(self._rtfm_cache[key].items())
        matches = fuzzy.finder(obj, cache, key=lambda t: t[0])[:10]

        e = discord.Embed(colour=Colors.BASE_COLOR)
        if len(matches) == 0:
            return await ctx.warn('Could not find anything. Sorry.')

        count = 1

        desc = []

        for key, url in matches:
            desc.append(f'\n`{count}` [`{key}`]({url})')
            count +=1
        
        e.description="".join(i for i in desc)
        e.set_author(
            name=ctx.author,
            icon_url=ctx.author.display_avatar.url
        )

        #e.description = '\n'.join(f'[`{key}`]({url})' for key, url in matches)
        await ctx.reply(embed=e)


    def transform_rtfm_language_key(self, ctx: Union[discord.Interaction, Context], prefix: str):
        return prefix

    @command(
            aliases=['rtfd', 'docs'],
            fallback='stable',
            name="rtfm",
            description="Gives you a documentation link for a discord.py entity"
    )
    async def rtfm(self, ctx: StealContext, *, entity: Optional[str] = commands.param(default=None, displayed_default=None)):
        await self.do_rtfm(ctx, 'stable', entity)

    @group(
            name="tag",
            description="Manage tags and shit."
    )
    async def tag(self, ctx: StealContext):
        if ctx.invoked_subcommand is None:
            name = ctx.message.content.split("tag ")[1]
            if name is None:
                return await ctx.deny(f'`{ctx.invoked_subcommand}` is not a valid subcommand of `tag`.')
            async with asqlite.connect("main.db") as conn:
                async with conn.cursor() as cursor:

                    await cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS tags(guildid INTEGER, ownerid INTEGER, name TEXT, script TEXT)
                        """
                    )

                    cur = await cursor.execute(
                        """
                        SELECT script FROM tags WHERE guildid = $1 AND name = $2
                        """, ctx.guild.id, name.lower(), 
                    )

                    script = await cur.fetchone()

                    if not script:
                        return await ctx.warn(f"Tag `{name}` not found.")
                    
                    scriptcode = script[0]

                    processed_message = EmbedBuilder.embed_replacement(ctx.author, scriptcode)
                    content, embed, view = await EmbedBuilder.to_object(processed_message)
                    await ctx.reply(content=content, embed=embed, view=view)

    @tag.command(
            name="create",
            descrtiption="Creates a tag."
    )
    @has_permissions(manage_messages=True)
    async def tagcreate(self, ctx: StealContext, name:str, *, script: str):
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tags(guildid INTEGER, ownerid INTEGER, name TEXT, script TEXT)
                    """
                )

                cur = await cursor.execute(
                    """
                    SELECT ownerid FROM tags WHERE guildid = $1 AND name = $2
                    """, ctx.guild.id, name.lower()
                )

                id = await cur.fetchone()

                if not id:

                    await cursor.execute(
                        """
                        INSERT INTO tags VALUES ($1, $2, $3, $4)
                        """, ctx.guild.id, ctx.author.id, name.lower(), script, 
                    )

                    await conn.commit()

                    return await ctx.approve(f"Created tag **{name.lower()}**.")
                
                else:
                    return await ctx.warn(f"The tag **{name.lower()}** already exists.")

    @tag.command(
            name="delete",
            descrtiption="Deletes a tag."
    )
    @has_permissions(manage_messages=True)
    async def tagdelete(self, ctx: StealContext, *, name: str):
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tags(guildid INTEGER, ownerid INTEGER, name TEXT, script TEXT)
                    """
                )

                cur = await cursor.execute(
                    """
                    SELECT ownerid FROM tags WHERE guildid = $1 AND name = $2
                    """, ctx.guild.id, name.lower()
                )

                id = await cur.fetchone()

                if not id:
                    return await ctx.warn(f"Tag **{name.lower()}** not found.")

                ownerid = id[0]
                if ownerid != ctx.author.id and ctx.author.id != ctx.guild.owner.id:
                    return await ctx.deny(f"You are not the owner of this tag.")

                await cursor.execute(
                    """
                    DELETE FROM tags WHERE guildid = $1 AND ownerid = $2 AND name = $3
                    """, ctx.guild.id, ownerid, name.lower(), 
                )

                return await ctx.approve(f"Deleted tag **{name.lower()}**.")

    @tag.command(
            name="list",
            descrtiption="Lists all server tags."
    )
    @has_permissions(manage_messages=True)
    async def taglist(self, ctx: StealContext):
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:

                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tags(guildid INTEGER, ownerid INTEGER, name TEXT, script TEXT)
                    """
                )

                cur = await cursor.execute(
                    """
                    SELECT name, ownerid FROM tags WHERE guildid = $1
                    """, ctx.guild.id, 
                )

                tags = await cur.fetchall()

                if not tags:
                    return await ctx.warn(f"There are no tags in this guild.")

                taglist = tags

                count = 0
                embeds = []
                """
                entries = [
                    f"{tagname} ({tagowner})"
                    for tagname, tagowner, in enumerate(taglist, start=1)
                ]"""
                entries = [
                        f"`{i}` **{tagname}** (<@{tagowner}>)"
                        for i, [tagname, tagowner] in enumerate(taglist, start=1)
                    ]
                    
                print(entries)

                l = 5

                embed = discord.Embed(
                    color=Colors.BASE_COLOR,
                    description="",
                    title=f"Tags (`{len(entries)}`)",
                ).set_footer(
                            icon_url=self.bot.user.display_avatar.url or None,
                            text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
                        )

                for entry in entries:
                    embed.description += f'{entry}\n'
                    count += 1

                    if count == l:
                        embeds.append(embed)
                        embed = discord.Embed(
                            color=Colors.BASE_COLOR,
                            title=f"Tags (`{len(entries)}`)",
                        ).set_footer(
                            icon_url=self.bot.user.display_avatar.url or None,
                            text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
                        )

                        count = 0

                if count > 0:
                    embeds.append(embed.set_footer(
                            icon_url=self.bot.user.display_avatar.url or None,
                            text=f'Page {len(embeds) + 1}/{math.ceil(len(entries) / l)} ({len(entries)} entries)'
                        ))

                await ctx.paginate(embeds)

    @command(
            name="embedui",
            description="Sends embed builder Ui",
            aliases=["uembed", "uem", "ems", "embedsetup"]
    )
    @has_permissions(administrator=True)
    @bot_has_guild_permissions(send_messages=True)
    @cooldown(2, 15, BucketType.user)
    async def embedui(
        self,
        ctx: StealContext,
        *,
        flags: Optional[typing.Literal['--help']],
    ):
        """Sends an embed using flags. An interactive embed maker is also available if you don't pass any flags.

        Parameters
        ----------
        flags: EmbedFlags
            The flags to use. Please see ``embed --help`` for flag info.
        """
        if flags is None:
            view = EmbedEditor(ctx.author, self)  # type: ignore

            if ctx.message.reference and ctx.message.reference.embeds:
                view.embed = Embed.from_dict(ctx.message.reference.embeds[0].to_dict())
                await view.update_buttons()
            view.message = await ctx.reply(embed=view.current_embed, view=view)
            return

        if flags == '--help':
            return await ctx.reply(embed=HORRIBLE_HELP_EMBED)

        embed = discord.Embed(title=flags.title, description=flags.description, colour=flags.color)

        if flags.field and len(flags.field) > 25:
            raise commands.BadArgument('You can only have up to 25 fields!')

        for f in flags.field or []:
            embed.add_field(name=f.name, value=f.value, inline=f.inline)

        if flags.thumbnail:
            embed.set_thumbnail(url=flags.thumbnail)

        if flags.image:
            embed.set_image(url=flags.image)

        if flags.author:
            embed.set_author(name=flags.author.name, url=flags.author.url, icon_url=flags.author.icon)

        if flags.footer:
            embed.set_footer(text=flags.footer.text, icon_url=flags.footer.icon or None)

        if not embed:
            raise commands.BadArgument('You must pass at least one of the necessary (marked with `*`) flags!')
        if len(embed) > 6000:
            raise commands.BadArgument('The embed is too big! (too much text!) Max length is 6000 characters.')

    @command(
            name='embed',
            description='Creates an embed using a script.',
            aliases=['em', 'ce'],
    )
    @has_permissions(manage_messages=True)
    @bot_has_guild_permissions(send_messages=True)
    @guild_only()
    async def embedsend(self, ctx: StealContext,reply:Optional[bool] = False, *, message:str) -> None:
        
        processed_message = EmbedBuilder.embed_replacement(ctx.author, message)
        content, embed, view = await EmbedBuilder.to_object(processed_message)
        if reply:
            return await ctx.reply(content=content, embed=embed, view=view)
        return await ctx.send(content=content, embed=embed, view=view)

    @command(
            name="embedcode",
            descrtiption="Sends code for an embed.",
            aliases=["ec"],
    )
    async def embedcode(self, ctx: StealContext) -> None:
        
        if not ctx.message.reference:
            return await ctx.warn(f"Respond to a message to fetch the embed code.")
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        await ctx.reply(f"```{EmbedBuilder().copy_embed(ref)}```")


    @command(
            name='dominant',
            aliases=["hex", "imagehex"]
    )
    async def dominant(self, ctx: StealContext, image: discord.Attachment):

        color = hex(await self.bot.dominant_color_url(image.url))[2:]
        hex_info = await self.bot.session.get_json(
            "https://www.thecolorapi.com/id", params={"hex": color}
        )
        hex_image = f"https://singlecolorimage.com/get/{color}/200x200"
        embed = (
            discord.Embed(color=int(color, 16))
            .set_author(icon_url=hex_image, name=hex_info["name"]["value"])
            .set_thumbnail(url=hex_image)
            .add_field(name="RGB", value=f'`{hex_info["rgb"]["value"]}`')
            .add_field(name="HEX", value=f'`{hex_info["hex"]["value"]}`')
        )

        await ctx.reply(embed=embed)

    @command(
            name='color',
    )
    async def color(self, ctx: StealContext, *, hexrgb:str):


        hex = None
        rgb = None
        if isHex(hexrgb.lstrip("#")):
            hex = hexrgb.split("#")[1]
            hex = list(hex) if hex else None
            if hex: del hex[6:]
            hex = "".join(hex)

        else:
            try:
                rgb = hexrgb.split("rgb(")[1].split(")")[0].replace(" ", "")
                values = [i for i in rgb.split(",")]

                for value in values:
                    if not int(value):
                        return await ctx.warn(f"`{hexrgb}` is not a valid color.")
                    if int(value) < 0 or int(value) > 255:
                        return await ctx.warn(f"`{hexrgb}` is not a valid color.")

                rgb = ",".join(values)

                def clamp(x):
                    return max(0, min(int(x), 255))
                fart = "{0:02x}{1:02x}{2:02x}".format(clamp(values[0]), clamp(values[1]), clamp(values[2]))

            except:
                return await ctx.warn(f"`{hexrgb}` is not a valid color.")

        inp = None
        inp = "hex" if hex else None
        inp = "rgb" if rgb else inp
        try:
            hex_info = await self.bot.session.get_json(
                "https://www.thecolorapi.com/id", params = {inp: hex if hex else rgb}
            )
        except:
            return await ctx.warn(f"`{hexrgb}` is not a valid color.")

        hex_image = f"https://singlecolorimage.com/get/{hex if hex else fart}/200x200"
        embed = (
            discord.Embed(color=int(hex_info["hex"]["value"].replace("#", ""), 16))
            .set_author(icon_url=hex_image, name=hex_info["name"]["value"])
            .set_thumbnail(url=hex_image)
            .add_field(name="RGB", value=f'`{hex_info["rgb"]["value"]}`')
            .add_field(name="HEX", value=f'`{hex_info["hex"]["value"]}`')
        )

        await ctx.reply(embed=embed)


    @command(
            name="avatar",
            description='Gets someones avatar.',
            aliases=['av', 'pfp'],
    )
    async def avatar(self, ctx: StealContext, member:Optional[discord.User] = commands.param(default=None, displayed_default=None)) -> None:
        if not member:member=ctx.author
        if not member.display_avatar:
            return await ctx.deny(f"**{member}** does not have an avatar.")

        await ctx.reply(
                embed=discord.Embed(
                    title=f"{member.display_name}'s avatar",
                    url=member.display_avatar.url, 
                    color=await self.bot.dominant_color_url(member.display_avatar.url),
                ).set_image(
                    url=member.display_avatar.url
                )
        )


    @command(
            name="banner",
            description='Gets someones avatar.',
    )
    async def banner(self, ctx: StealContext, member:Optional[discord.User] = commands.param(default=None, displayed_default=None)) -> None:
        if not member:member=ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            await ctx.reply(
                    embed=discord.Embed(
                        title=f"{user.display_name}'s banner", 
                        url=user.banner.url, 
                        color=await self.bot.dominant_color_url(user.banner.url)
                    ).set_image(
                        url=user.banner
                    )
            )
        else:
            return await ctx.reply(embed=discord.Embed(
                title=f"{member.display_name}'s banner color: {user.accent_color}", color=user.accent_color
                ))

    @command(
            name="afk",
            description="Sets your afk status"
    )
    async def afk(self, ctx: StealContext, *, status:Optional[str] = "None") -> None:
        async with asqlite.connect("main.db") as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS afk(guildid INTEGER, userid INTEGER, status TEXT, time INTEGER)"
                )

                await cursor.execute(
                    "INSERT INTO afk (guildid, userid, status, time) VALUES ($1, $2, $3, $4)",
                    ctx.guild.id, ctx.author.id, status, datetime.datetime.now().timestamp(),
                )

                await conn.commit()
                await ctx.approve(f"You are now AFK with the status - **{status}**")

    @command(
            name="compress",
            description="Compresses an image"
    )
    @cooldown(1,15, BucketType.user)
    async def imgcompress(self, ctx: StealContext, image: discord.Attachment):
        bytes = await image.read()
        size = sys.getsizeof(bytes)
        compbytes = compress_image(bytes)
        newsize = sys.getsizeof(compbytes)

        file = discord.File(io.BytesIO(compbytes), filename=f"compressed-{image.filename.split(".")[0]}.{image.filename.split(".")[1]}")

        name = list(image.filename.split('.')[0])
        print(len(name))
        if len(name) > 14:
            i = len(name) - 14
            for l in range(0, i):
                name.pop()
            name.append('...')

        embed=discord.Embed(
            title=f"Compressed {''.join(name)}",
            color=await self.bot.dominant_color(compbytes),
        ).set_image(
                url=f"attachment://compressed-{image.filename.split(".")[0]}.{image.filename.split(".")[1]}"
        ).set_footer(
            text=f"{math.floor(newsize/1000)}kb - saved {math.floor(size/1000 - newsize/1000)}kb"
        )
        
        await ctx.send(
            file = file,
            embed=embed
        )

    @command(
            name="bytes",
            description="Sends the image bytes of a link"
    )
    @cooldown(1,15, BucketType.user)
    async def bytes(self, ctx: StealContext, url: str): 
        bytes = await self.bot.session.get_bytes(url)

        file = discord.File(io.BytesIO(bytes), filename=f"bytes.png")

        embed=discord.Embed(
            title=f"Image Bytes",
            color=await self.bot.dominant_color(bytes),
        ).set_image(
                url=f"attachment://bytes.png"
        )
        
        await ctx.send(
            file = file,
            embed=embed
        )	

    @command(
            name="snipe",
            aliases=["s"],
            description="Get the most recent deleted messages in the channel."
    )
    async def snipe(self, ctx: StealContext, index: int = 1):

        try:
            if not self.bot.cache.get("snipe"):
                return await ctx.warn("I could not find any **snipes** in this channel.")
            snipes = [
                s for s in self.bot.cache.get("snipe") if s["channel"] == ctx.channel.id
            ]
            if len(snipes) == 0:
                return await ctx.warn("I could not find any **snipes** in this channel.")
            if index > len(snipes):
                return await ctx.warn(
                    f"There are only `{len(snipes)}` **snipes** in this channel"
                )
            result = snipes[::-1][index - 1]
            embed = (
                discord.Embed(
                    color=Colors.BASE_COLOR,
                    description=f"> {result['message']}",
                    timestamp=datetime.datetime.fromtimestamp(
                        result["created_at"]
                    ).replace(tzinfo=None),
                )
                .set_author(name=result["name"], icon_url=result["avatar"])
                .set_footer(text=f"{index}/{len(snipes)}")
            )

            if len(result["stickers"]) > 0:
                sticker: discord.StickerItem = result["stickers"][0]
                embed.set_image(url=sticker.url)
            else:
                if len(result["attachments"]) > 0:
                    attachment: discord.Attachment = result["attachments"][0]
                    if ".mp4" in attachment.filename or ".mov" in attachment.filename:
                        file = discord.File(
                            io.BytesIO(await attachment.read()),
                            filename=attachment.filename,
                        )
                        return await ctx.send(embed=embed, file=file)
                    else:
                        embed.set_image(url=attachment.url)

            return await ctx.send(embed=embed)
        except Exception as e:
            return await ctx.warn("An error occured when fetching **snipes**.")

    @command(
            name="editsnipe",
            description="Get the most recent edited messages.",
            aliases=["es"]
    )
    async def editsnipe(self, ctx: StealContext, index: int = 1):
        try:

            if not self.bot.cache.get("edit_snipe"):
                return await ctx.warn("I could not find any **edit snipes** in this channel")

            snipes = [
                s for s in self.bot.cache.get("edit_snipe") if s["channel"] == ctx.channel.id
            ]

            if len(snipes) == 0:
                return await ctx.warn("I could not find any **edit snipes** in this channel")

            if index > len(snipes):
                return await ctx.warn(
                    f"There are only `{len(snipes)}` **edit snipes** in this channel"
                )

            result = snipes[::-1][index - 1]
            embed = (
                discord.Embed(
                        color=Colors.BASE_COLOR,
                        timestamp=datetime.datetime.fromtimestamp(
                            result["edited_at"]
                        ).replace(tzinfo=None),
                )
                .set_author(name=result["name"], icon_url=result["avatar"])
                .set_footer(text=f"{index}/{len(snipes)}")
            )

            for m in ["before", "after"]:
                embed.add_field(name=m.capitalize(), value=f"> **{result[m]}**", inline=False)

            return await ctx.send(embed=embed)
        except Exception as e:
            return await ctx.warn("An error occured when fetching **edit snipes**.")

    @command(
            name="reactionsnipe",
            description="Get the most recent reaction.",
            aliases=["rs"]
    )
    async def reactionsnipe(self, ctx: StealContext, index: int = 1):

        if not self.bot.cache.get("reaction_snipe"):
            return await ctx.warn("I could not find any **reaction snipes** in this channel")

        snipes = [
            s
            for s in self.bot.cache.get("reaction_snipe")
            if s["channel"] == ctx.channel.id
        ]

        if len(snipes) == 0:
            return await ctx.warn("I could not find any **reaction snipes** in this channel")

        if index > len(snipes):
            return await ctx.warn(
                f"There are only **{len(snipes)}** reaction snipes in this channel"
            )

        result = snipes[::-1][index - 1]
        try:
            message = await ctx.channel.fetch_message(result["message"])
            return await ctx.reply(
                f"**{result['name']}** reacted with {result['reaction']} **{self.bot.humanize_date(datetime.datetime.fromtimestamp(int(result['created_at'])))}** [**here**]({message.jump_url})"
            )
        except:
            return await ctx.reply(
                f"**{result['name']}** reacted with {result['reaction']} **{self.bot.humanize_date(datetime.datetime.fromtimestamp(int(result['created_at'])))}**"
            )

    @command(
            name="clearsnipes",
            aliases=["cs"],
            description="Clears all sniped messages for this channel."
    )
    @has_guild_permissions(manage_messages=True)
    async def clearsnipes(self, ctx: StealContext):
        """
        Clear the snipes from the channel
        """

        for i in ["snipe", "edit_snipe", "reaction_snipe"]:
            snipes = self.bot.cache.get(i)

            if snipes:
                
                sdata = [m for m in snipes if m["channel"] == ctx.channel.id]

                if not sdata:
                    return await ctx.warn("There are no **snipes** in this channel.")

                for s in sdata:
                    snipes.remove(s)
                await self.bot.cache.set(i, snipes)

        await ctx.approve("Cleared all snipes from this channel")

    @command(
            name="firstmessage",
            aliases=["firstmsg"],
            description="Get the first message in a channel."
    )
    async def firstmessage(self, ctx: StealContext, *, channel: discord.TextChannel = commands.CurrentChannel):

        message = [mes async for mes in channel.history(limit=1, oldest_first=True)][0]
        await ctx.approve(
            f"The first [**message**]({message.jump_url}) sent in {channel.mention if not isinstance(channel, discord.DMChannel) else "this dm."}"
        )


    @group(
            name="reminder",
            aliases=["r"],
            description="The reminder module."
    )
    async def reminder(self, ctx: StealContext):
        if ctx.invoked_subcommand is None:		
            pass
    
    @command(
            name="remindme",
            description="Set a reminder for yourself.",
            aliases=["rm"]
    )
    async def remindme(self, ctx: StealContext, time:ValidTime, *, task:Optional[str] = None) -> None:
        await self.reminderset(ctx,time,task)


    @reminder.command(
            name="set",
            description="Set a reminder for yourself."
    )
    async def reminderset(self, ctx: StealContext, time:ValidTime, *, task:Optional[str] = "Nothing ig?") -> None:
        async with asqlite.connect("main.db") as db:
            async with db.cursor() as cursor:
                
                if time < 60:
                    return await ctx.warn("You can't have a **reminder** set for **less** than a minute.")

                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS reminder(guildid INTEGER, userid INTEGER, channelid INTEGER, time INTEGER, task TEXT)"
                )

                cur = await cursor.execute(
                    "SELECT * FROM reminder WHERE userid = $1 AND guildid = $2 AND channelid = $3",
                    ctx.author.id, ctx.guild.id, ctx.channel.id, 
                )

                results = await cur.fetchone()

                if results:
                    return await ctx.warn(f"You already have a **reminder** in this **channel** - **{results[4]}** in {humanize.precisedelta(datetime.datetime.fromtimestamp(results[3]), format=f'%0.0f')}.")
                
                await db.execute(
                    "INSERT INTO reminder VALUES ($1, $2, $3, $4, $5)",
                    ctx.guild.id, ctx.author.id, ctx.channel.id, (datetime.datetime.now() + datetime.timedelta(seconds=time)).timestamp(), task,
                )
                await db.commit()

                await ctx.reply(
                    embed=discord.Embed(
                        description=f"> {Emojis.TIME} {ctx.author.mention}: I will remind you in {humanfriendly.format_timespan(time)} about **{task}**",
                        color=Colors.BASE_COLOR
                    )
                )

    @reminder.command(
            name="stop",
            description="Deletes the reminder you have in the current channel.",
            aliases=["delete", "remove"]
    )
    async def reminderstop(self, ctx: StealContext):
        async with asqlite.connect("main.db") as db:
            async with db.cursor() as cursor:

                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS reminder(guildid INTEGER, userid INTEGER, channelid INTEGER, time INTEGER, task TEXT)"
                )

                cur = await cursor.execute(
                    "SELECT * FROM reminder WHERE userid = $1 AND guildid = $2 AND channelid = $3",
                    ctx.author.id, ctx.guild.id, ctx.channel.id
                )

                results = await cur.fetchone()

                if not results:
                    return await ctx.warn("You don't have a **reminder** set in this **channel**.")	

                await db.execute(
                    "DELETE FROM reminder WHERE userid = $1 AND channelid = $2",
                    ctx.author.id, ctx.channel.id
                )	
                await db.commit()

                await ctx.approve(f"Deleted **reminder** - **{results[4]}** in {humanize.precisedelta(datetime.datetime.fromtimestamp(results[3]), format=f'%0.0f')}")

async def setup(bot):
    await bot.add_cog(Utility(bot))
