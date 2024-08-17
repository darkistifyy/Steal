from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Optional, Any, TypeAlias, Self

import asyncpg
from discord.ui import *
import discord
from discord import ButtonStyle
from discord.ext import commands
from tools.Config import Emojis, Colors

from .modals import (
    AddFieldModal,
    EditAuthorModal,
    EditEmbedModal,
    EditFieldModal,
    EditFooterModal,
    EditWithModalButton,
)

import utils

if TYPE_CHECKING:
    from ...managers.interaction import PatchedInteraction

    from . import Information

    BotInteraction: TypeAlias = discord.Interaction[PatchedInteraction]


class Embed(discord.Embed):
    def __bool__(self) -> bool:
        return any(
            (
                self.title,
                self.url,
                self.description,
                self.fields,
                self.timestamp,
                self.author,
                self.thumbnail,
                self.footer,
                self.image,
            )
        )



class UndoView(discord.ui.View):
    def __init__(self, parent: 'EmbedEditor'):
        self.parent = parent
        super().__init__(timeout=10)

    @discord.ui.button(label='Undo deletion.')
    async def undo(self, interaction: BotInteraction, button: discord.ui.Button[UndoView]):
        self.stop()
        await interaction.channel.send(view=self.parent, embed=self.parent.current_embed)  # type: ignore
        await interaction.response.edit_message(view=None)
        await interaction.delete_original_response()

    async def on_timeout(self) -> None:
        self.parent.stop()


class DeleteButton(discord.ui.Button['EmbedEditor']):
    async def callback(self, interaction: BotInteraction):  # pyright: ignore[reportIncompatibleMethodOverride]
        if interaction.message:
            await interaction.message.delete()
        await interaction.response.send_message(
            'Done!\n*This message goes away in 10 seconds*\n*You can use this to recover your progress.*',
            view=UndoView(self.view),  # type: ignore
            delete_after=10,
            ephemeral=True,
        )


class FieldSelectorView(discord.ui.View):
    def __init__(self, parent_view: EmbedEditor):
        self.parent = parent_view
        super().__init__(timeout=300)
        self.update_options()

    def update_options(self):
        self.pick_field.options = []
        for i, field in enumerate(self.parent.embed.fields):
            self.pick_field.add_option(label=f"{i + 1}) {(field.name or '')[0:95]}", value=str(i))

    @discord.ui.select(placeholder='Select a field to delete.')
    async def pick_field(self, interaction: BotInteraction, select: discord.ui.Select):
        await self.actual_logic(interaction, select)

    @discord.ui.button(label='Go back')
    async def cancel(self, interaction: BotInteraction, button: discord.ui.Button[Self]):
        await interaction.response.edit_message(view=self.parent)
        self.stop()

    async def actual_logic(self, interaction: BotInteraction, select: discord.ui.Select[Self]) -> None:
        raise NotImplementedError('Child classes must overwrite this method.')


class DeleteFieldWithSelect(FieldSelectorView):
    async def actual_logic(self, interaction: BotInteraction, select: discord.ui.Select[Self]):
        index = int(select.values[0])
        self.parent.embed.remove_field(index)
        await self.parent.update_buttons()
        await interaction.response.edit_message(embed=self.parent.current_embed, view=self.parent)
        self.stop()


class EditFieldSelect(FieldSelectorView):
    async def actual_logic(self, interaction: BotInteraction, select: discord.ui.Select[Self]):
        index = int(select.values[0])
        self.parent.timeout = 600
        await interaction.response.send_modal(EditFieldModal(self.parent, index))


class SendToView(discord.ui.View):
    def __init__(self, *, parent: EmbedEditor):
        self.parent = parent
        super().__init__(timeout=300)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[
            discord.ChannelType.text,
            discord.ChannelType.news,
            discord.ChannelType.voice,
            discord.ChannelType.private_thread,
            discord.ChannelType.public_thread,
        ],
    )
    async def pick_a_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect[SendToView]):
        await interaction.response.defer(ephemeral=True)
        channel = select.values[0]
        if not isinstance(interaction.user, discord.Member) or not interaction.guild:
            return await interaction.followup.send(
                'for some reason, discord thinks you are not a member of this server...', ephemeral=True
            )
        channel = interaction.guild.get_channel_or_thread(channel.id)
        if not isinstance(channel, discord.abc.Messageable):
            return await interaction.followup.send('That channel does not exist... somehow.', ephemeral=True)
        if not channel.permissions_for(interaction.user).send_messages:
            return await interaction.followup.send('You cannot send messages in that channel.', ephemeral=True)
        await channel.send(embed=self.parent.embed)
        await interaction.delete_original_response()
        await interaction.followup.send('Sent!', ephemeral=True)
        self.stop()

    @discord.ui.button(label='Go Back')
    async def stop_pages(self, interaction: discord.Interaction, button: discord.ui.Button[SendToView]):
        """stops the pagination session."""
        await interaction.response.edit_message(embed=self.parent.current_embed, view=self.parent)
        self.stop()

    async def on_timeout(self) -> None:
        self.parent.cog.bot.views.discard(self)
        if self.parent.message:
            try:
                await self.parent.message.edit(view=self.parent)
            except discord.NotFound:
                pass


class EmbedEditor(discord.ui.View):
    def __init__(self, owner: discord.Member, cog: Information, *, timeout: Optional[float] = 600):
        self.cog: Information = cog
        self.owner: discord.Member = owner
        self.embed = Embed()
        self.showing_help = False
        self.message: Optional[discord.Message] = None
        super().__init__(timeout=timeout)
        self.clear_items()
        self.add_items()

    @staticmethod
    def shorten(_embed: discord.Embed):
        embed = Embed.from_dict(deepcopy(_embed.to_dict()))
        while len(embed) > 6000 and embed.fields:
            embed.remove_field(-1)
        if len(embed) > 6000 and embed.description:
            embed.description = embed.description[: (len(embed.description) - (len(embed) - 6000))]
        return embed

    @property
    def current_embed(self) -> discord.Embed:
        if self.showing_help:
            return self.help_embed()
        if self.embed:
            if len(self.embed) < 6000:
                return self.embed
            else:
                return self.shorten(self.embed)
        return self.help_embed()

    async def interaction_check(self, interaction: BotInteraction, /):  # pyright: ignore[reportIncompatibleMethodOverride]
        if interaction.user == self.owner:
            return True
        await interaction.response.send_message('This is not your menu.', ephemeral=True)

    def add_items(self):
        """This is done this way because if not, it would get too cluttered."""
        # Row 1
        self.add_item(discord.ui.Button(label='Edit:', style=ButtonStyle.blurple, disabled=True))
        self.add_item(EditWithModalButton(EditEmbedModal, label='Embed', style=ButtonStyle.blurple))
        self.add_item(EditWithModalButton(EditAuthorModal, row=0, label='Author', style=ButtonStyle.blurple))
        self.add_item(EditWithModalButton(EditFooterModal, row=0, label='Footer', style=ButtonStyle.blurple))
        self.add_item(DeleteButton(emoji='\N{WASTEBASKET}', style=ButtonStyle.red))
        # Row 2
        self.add_item(discord.ui.Button(row=1, label='Fields:', disabled=True, style=ButtonStyle.blurple))
        self.add_fields = EditWithModalButton(AddFieldModal, row=1, emoji='\N{HEAVY PLUS SIGN}', style=ButtonStyle.green)
        self.add_item(self.add_fields)
        self.add_item(self.remove_fields)
        self.add_item(self.edit_fields)
        self.add_item(self.reorder)
        # Row 3
        self.add_item(self.send)
        self.add_item(self.send_to)
        #self.add_item(self.help_page)
        # Row 4
        self.character_count: discord.ui.Button[Self] = discord.ui.Button(row=3, label='0/6,000 Characters', disabled=True)
        self.add_item(self.character_count)
        self.fields_count: discord.ui.Button[Self] = discord.ui.Button(row=3, label='0/25 Total Fields', disabled=True)
        self.add_item(self.fields_count)

    async def update_buttons(self):
        fields = len(self.embed.fields)
        if fields > 25:
            self.add_fields.disabled = True
        else:
            self.add_fields.disabled = False
        if not fields:
            self.remove_fields.disabled = True
            self.edit_fields.disabled = True
            self.reorder.disabled = True
        else:
            self.remove_fields.disabled = False
            self.edit_fields.disabled = False
            self.reorder.disabled = False
        if self.embed:
            if len(self.embed) <= 6000:
                self.send.style = ButtonStyle.green
                self.send_to.style = ButtonStyle.green
            else:
                self.send.style = ButtonStyle.red
                self.send_to.style = ButtonStyle.red
        else:
            self.send.style = ButtonStyle.red
            self.send_to.style = ButtonStyle.red

        self.character_count.label = f"{len(self.embed)}/6,000 Characters"
        self.fields_count.label = f"{len(self.embed.fields)}/25 Total Fields"


    def help_embed(self) -> Embed:
        embed = Embed(
            title='__`M⬇`__ This is the embed title',
            color=Colors.BASE_COLOR,
            description=(
                "Create your embed"),
        )
        if not self.embed and not self.showing_help:
            footer_text += '\n💢This embed will be replaced by yours once it has characters💢'
        embed.set_footer(icon_url='https://cdn.duck-bot.com/file/ICON', text=footer_text)
        return embed

    @discord.ui.button(row=1, emoji='\N{HEAVY MINUS SIGN}', style=ButtonStyle.red, disabled=True)
    async def remove_fields(self, interaction: BotInteraction, button: discord.ui.Button[Self]):
        await interaction.response.edit_message(view=DeleteFieldWithSelect(self))

    @discord.ui.button(row=1, emoji=Emojis.NAVIGATE_PAGINATOR, disabled=True, style=ButtonStyle.green)
    async def edit_fields(self, interaction: BotInteraction, button: discord.ui.Button[Self]):
        await interaction.response.edit_message(view=EditFieldSelect(self))

    @discord.ui.button(row=1, label='Reorder', style=ButtonStyle.blurple, disabled=True)
    async def reorder(self, interaction: BotInteraction, button: discord.ui.Button[Self]):
        return await interaction.response.send_message(
            f'This function is currently unavailable.\nPlease use {Emojis.NAVIGATE_PAGINATOR} and edit the `index`',
            ephemeral=True,
        )

    @discord.ui.button(label='Send', row=2, style=ButtonStyle.red)
    async def send(self, interaction: BotInteraction, button: discord.ui.Button[Self]):
        if not self.embed:
            return await interaction.response.send_message('Your embed is empty!', ephemeral=True)
        elif len(self.embed) > 6000:
            return await interaction.response.send_message(
                'You have exceeded the embed character limit (6000)', ephemeral=True
            )
        await interaction.channel.send(embed=self.embed)  # type: ignore
        await interaction.response.defer()
        await interaction.delete_original_response()

    @discord.ui.button(label='Send To', row=2, style=ButtonStyle.red)
    async def send_to(self, interaction: BotInteraction, button: discord.ui.Button[Self]):
        if not self.embed:
            return await interaction.response.send_message('Your embed is empty!', ephemeral=True)
        elif len(self.embed) > 6000:
            return await interaction.response.send_message(
                'You have exceeded the embed character limit (6000)', ephemeral=True
            )
        await interaction.response.edit_message(view=SendToView(parent=self))
