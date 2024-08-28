import discord

from discord.ext.commands import HelpCommand
import discord.ext.commands
from discord.ext.commands.cog import Cog
from discord.ext.commands.core import Command, Group
from discord.ext import commands
from discord.ext.commands import *

from typing import Any, Callable, Dict, List, Mapping

import discord.ext
from tools.Config import Colors, Guild
from managers.interaction import PatchedInteraction


class StealHelp(HelpCommand):
    def __init__(self):
        super().__init__()
        self.command_attrs = {
            'aliases': ['assist', 'commands']
        }
        self.verify_checks = True
        
    async def send_bot_help(self, mapping: Mapping[Cog, List[Command[Any, Callable[..., Any], Any]]]) -> None:
        view = discord.ui.View(timeout = 180)
        embed = discord.Embed(
            color = Colors.BASE_COLOR,
        ).set_author(
                name = f"{self.context.bot.user.name.split('#')[0]} command menu",
                icon_url = self.context.author.display_avatar.url if self.context.author.display_avatar else None
        ).set_thumbnail(
                url = self.context.bot.user.display_avatar.url
        ).set_footer(
                text="Select a cog from the dropdown menu below"
        ).add_field(
            name="Information",
            value="> [] = optional, <> = required"
        ).add_field(
            name="Support",
            value=f"[**Support server**]({Guild.INVITE})"
        )
        

        
        async def interaction_check(interaction: PatchedInteraction) -> bool:
            if interaction.user.id != self.context.author.id:
                await interaction.warn("You're not the **author** of this embed!")
                
            return interaction.user.id == self.context.author.id
        
        view.interaction_check = interaction_check
        
        view.add_item(CategorySelector({key.__cog_name__: key for key, _ in mapping.items() if key is not None and key.__cog_name__ not in ["BotManagement", "Auth", "Bs", "Help", "Profile", "Messages", "Members", "Jishaku"]}, embed))
        
        return await self.context.send(
            embed = embed,
            view = view
        )
    
    async def command_help(self, command: Command) -> None:
        return await self.context.send_help(command.qualified_name)
        
    async def send_command_help(self, command: Command) -> None:
        if command.hidden and self.context.author.id not in self.context.bot.owner_ids: 
            return
        
        prefix = self.context.clean_prefix
        return await self.context.send(
            embed = discord.Embed(
                color = Colors.BASE_COLOR,
                title = f'Command: {command.qualified_name}',
                description = f'>>> {command.description or "No Description Provided"}'
            )
            .set_author(name = self.context.author.display_name, icon_url = self.context.author.display_avatar.url)
            .add_field(name = 'Aliases', value = ', '.join(command.aliases) or 'N/A', inline = True)
            .add_field(name = 'Parameters', value = ', '.join([parameter for parameter in command.params] or 'N/A'), inline = True)
            .add_field(name = 'Usage', value = f'>>> ```ruby\nSyntax: {prefix}{command.qualified_name} {command.signature.strip("= None").replace(" (upload a file)", "")}```', inline = False)
            .set_footer(text = f'Module: {command.cog_name}', icon_url = self.context.bot.user.display_avatar.url)
        )
        
    async def command_help(self, command: Command) -> Any:
        return await self.context.send_help(command.qualified_name)
        
    def command_not_found(self, string: str) -> str:
        return f"Command `{string}` does not exist"
    
    def subcommand_not_found(self, command: Command, string: str) -> str:
        return f"Command `{command.qualified_name} {string}` does not exist"
    
    async def send_error_message(self, error: str) -> None:
        return await self.context.deny(error)
        
    async def send_group_help(self, group: Group) -> None:
        if group.hidden and self.context.author.id not in self.context.bot.owner_ids: 
            return
        
        prefix = self.context.clean_prefix
        group_commands = []
        for command in group.commands:
            if isinstance(command, discord.ext.commands.Group): group_commands = [*group_commands, command, *command.commands]
        commands = [group, *[command for command in group.commands if not isinstance(command, discord.ext.commands.Group)], *group_commands]
                
        return await self.context.paginate([
            discord.Embed(
                color = Colors.BASE_COLOR,
                title = f'Group Command: {command.qualified_name}',
                description = f'>>> {command.description or "No Description Provided"}'
            )
                .set_author(name = self.context.author.display_name, icon_url = self.context.author.display_avatar.url)
                .add_field(name = 'Aliases', value = ', '.join(command.aliases) or 'N/A', inline = True)
                .add_field(name = 'Parameters', value = ', '.join([parameter for parameter in command.params] if not isinstance(command, Group) else [parameter.name for parameter in group.commands]) or 'N/A', inline = True)
                .add_field(name = 'Usage', value = f'>>> ```ruby\nSyntax: {prefix}{command.qualified_name} {command.signature.strip("= None").replace(" (upload a file)", "")}```', inline = False)
                .set_footer(text = f'Page {i + 1}/{len(commands)} ({len(commands)} entries) ∙ Module: {command.cog_name}', icon_url = self.context.bot.user.display_avatar.url)
            for i, command in enumerate(commands)
        ])

class CategorySelector(discord.ui.Select):
    def __init__(self, categories: Dict[str, Cog], embed: discord.Embed) -> None:
        self.embed = embed
        self.categories = categories
        super().__init__(
            placeholder='Select a Category',    
            options=[
                discord.SelectOption(label = 'Home', description = 'Beginning help page.', value = 'home'),
                *[discord.SelectOption(label = key, description = category.description, value = key) for key, category in categories.items()]
            ]
        )
        
    async def callback(self, interaction: discord.Interaction) -> None:
        if self.values[0] == 'home':
            return await interaction.response.edit_message(
                embed = self.embed
            )
            
        category: Cog = self.categories[self.values[0]]
        #commands = [command for command in list(category.walk_commands()) if not command.parent]
        commands = [command for command in list(category.walk_commands()) if not command.parent]
        subcommands = [sub for sub in list(category.walk_commands()) if sub.parent]
        
        description = f'```{", ".join(f"{sub.qualified_name}" for sub in subcommands)}'

        description = f"{description}\n\n{', '.join(f'{cmd.name}*' for cmd in commands if isinstance(cmd, discord.ext.commands.Group))}"

        description = f"{description}, {', '.join(f'{cmd.qualified_name}' for cmd in commands if not isinstance(cmd, discord.ext.commands.Group))}```"

        embed = self.embed.copy()
        embed.title = f'Category: {category.__cog_name__}'
        #embed.description = f'\nCommands:\n```{", ".join([f"{command.name}" if not isinstance(command, discord.ext.commands.Group) else f"{command.qualified_name}*" for command in list(category.walk_commands()) if not command.hidden])}```'
        embed.description = description
        embed.set_footer(
                text=f"{len(commands)} commands."
        ).set_author(
                name=f"{interaction.message.author.name.split('#')[0]} command menu",
                icon_url=interaction.user.display_avatar.url
        )
        return await interaction.response.edit_message(
            embed = embed
        )
    
