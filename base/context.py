from __future__ import annotations

from base.config import *
from base.managers.paginator import *
from discord.ext.commands import HelpCommand, Group
from datetime import datetime
from xxhash import xxh32_hexdigest

from discord.ext.commands import Command, Group


from typing import Union
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Unpack, TypedDict, cast

from discord import (
    AllowedMentions,
    ButtonStyle,
    Color,
    Message,
    MessageReference,
    Embed,
    Role,
    Member,
    SelectOption,
    ui,
)
from discord.ui import View, Button
from discord.ui import button
from discord.ext.commands import Context as BaseContext
from base.config import *

if TYPE_CHECKING:
    from base.grief import Bot


class FieldDict(TypedDict, total=False):
    name: str
    value: str
    inline: bool


class FooterDict(TypedDict, total=False):
    text: Optional[str]
    icon_url: Optional[str]


class AuthorDict(TypedDict, total=False):
    name: Optional[str]
    icon_url: Optional[str]


class ButtonDict(TypedDict, total=False):
    url: Optional[str]
    emoji: Optional[str]
    style: Optional[ButtonStyle]
    label: Optional[str]


class MessageKwargs(TypedDict, total=False):
    content: Optional[str]
    tts: Optional[bool]
    allowed_mentions: Optional[AllowedMentions]
    reference: Optional[MessageReference]
    mention_author: Optional[bool]
    delete_after: Optional[float]

    # Embed Related
    url: Optional[str]
    title: Optional[str]
    color: Optional[Color]
    image: Optional[str]
    description: Optional[str]
    thumbnail: Optional[str]
    footer: Optional[FooterDict]
    author: Optional[AuthorDict]
    fields: Optional[List[FieldDict]]
    timestamp: Optional[datetime]
    view: Optional[View]
    buttons: Optional[List[ButtonDict]]


class Context(BaseContext):
    bot: "Bot"

    def is_dangerous(self, role: Role) -> bool:
        permissions = role.permissions

        return any(
            [
                permissions.kick_members,
                permissions.ban_members,
                permissions.administrator,
                permissions.manage_channels,
                permissions.manage_guild,
                permissions.manage_messages,
                permissions.manage_roles,
                permissions.manage_webhooks,
                permissions.manage_emojis_and_stickers,
                permissions.manage_threads,
                permissions.mention_everyone,
                permissions.moderate_members,
            ]
        )

    async def embed(self, **kwargs: Unpack[MessageKwargs]) -> Message:
        return await self.send(**self.create(**kwargs))

    def create(self, **kwargs: Unpack[MessageKwargs]) -> Dict[str, Any]:
        """Create a message with the given keword arguments.

        Returns:
            Dict[str, Any]: The message content, embed, view and delete_after.
        """
        view = View()

        for button in kwargs.get("buttons") or []:
            if not button or not button.get("label"):
                continue

            view.add_item(
                Button(
                    label=button.get("label"),
                    style=button.get("style") or ButtonStyle.secondary,
                    emoji=button.get("emoji"),
                    url=button.get("url"),
                )
            )

        embed = (
            Embed(
                url=kwargs.get("url"),
                description=kwargs.get("description"),
                title=kwargs.get("title"),
                color=kwargs.get("color") or COLORS.neutral,
                timestamp=kwargs.get("timestamp"),
            )
            .set_image(url=kwargs.get("image"))
            .set_thumbnail(url=kwargs.get("thumbnail"))
            .set_footer(
                text=cast(dict, kwargs.get("footer", {})).get("text"),
                icon_url=cast(dict, kwargs.get("footer", {})).get("icon_url"),
            )
            .set_author(
                name=cast(dict, kwargs.get("author", {})).get("name", ""),
                icon_url=cast(dict, kwargs.get("author", {})).get("icon_url", ""),
            )
        )

        for field in kwargs.get("fields") or []:
            if not field:
                continue

            embed.add_field(
                name=field.get("name"),
                value=field.get("value"),
                inline=field.get("inline", False),
            )

        return {
            "content": kwargs.get("content"),
            "embed": embed,
            "view": kwargs.get("view") or view,
            "delete_after": kwargs.get("delete_after"),
        }

    async def approve(self, message: str, **kwargs) -> Message:
        return await self.send(
            embed=Embed(
                color=COLORS.approve,
                description=f"{EMOJIS.APPROVE} {self.author.mention}: {message}",
            ),
            **kwargs,
        )

    async def warn(self, message: str, **kwargs) -> Message:
        return await self.send(
            embed=Embed(
                color=COLORS.warn,
                description=f"{EMOJIS.WARN} {self.author.mention}: {message}",
            ),
            **kwargs,
        )

    async def deny(self, message: str, **kwargs) -> Message:
        return await self.send(
            embed=Embed(
                color=COLORS.deny,
                description=f"{EMOJIS.DENY} {self.author.mention}: {message}",
            ),
            **kwargs,
        )

    async def cooldown(self, message: str, **kwargs) -> Message:
        return await self.send(
            embed=Embed(
                color=0x38A9E1,
                description=f"{EMOJIS.COOLDOWN} {self.author.mention}: {message}",
            )
        )

    async def paginate(self, embeds: List[discord.Embed], **kwargs) -> Message:
        if len(embeds) == 1:
            if isinstance(embeds[0], discord.Embed):
                return await self.send(embed=embeds[0])

        return await self.send(embed=embeds[0], view=Paginator(self, embeds), **kwargs)


class GriefHelp(HelpCommand):
    context: "Context"

    def __init__(self, **options):
        super().__init__(
            command_attrs={"aliases": ["h", "cmds", "commands"], "hidden": True},
            verify_checks=False,
            **options,
        )

    async def send_bot_help(self, mapping):
        modules: Dict[str, List[Command]] = {}
        is_bot_owner = await self.context.bot.is_owner(self.context.author)

        for cog, command_list in mapping.items():
            module_name = getattr(cog, "qualified_name", None) or "General"
            if module_name.casefold() == "jishaku" or (
                module_name.casefold() == "owner" and not is_bot_owner
            ):
                continue

            visible_commands: Dict[str, Command] = {}

            def add_command(command: Command) -> None:
                if command.hidden:
                    return
                visible_commands[command.qualified_name] = command
                if isinstance(command, Group):
                    for child in command.commands:
                        add_command(child)

            for command in command_list:
                add_command(command)

            if visible_commands:
                modules[module_name] = sorted(
                    visible_commands.values(),
                    key=lambda command: command.qualified_name.casefold(),
                )

        modules = dict(sorted(modules.items(), key=lambda item: item[0].casefold()))
        view = HelpMenuView(self.context, modules)
        await self.context.send(view=view)

    async def send_command_help(self, command: Command):
        aliases = command.aliases

        try:
            permissions = command.permissions  # type: ignore
        except (AttributeError, TypeError):
            permissions = []

        embed = (
            Embed(
                color=COLORS.neutral,
                title=f"Command: {command.qualified_name}",
                description=command.help or "No description provided",
            )
            .set_author(
                name=self.context.author.name,
                icon_url=self.context.author.display_avatar.url,
            )
            .add_field(
                name="Aliases",
                value=", ".join(aliases) if aliases else "N/A",
                inline=True,
            )
            .add_field(
                name="Parameters",
                value=(
                    ", ".join(command.clean_params) if command.clean_params else "N/A"
                ),
                inline=True,
            )
            .add_field(
                name="Information",
                value=f"{EMOJIS.WARN} "
                + (", ".join(permissions) if permissions else "N/A"),
                inline=True,
            )
            .add_field(
                name="Usage",
                value=f"```Syntax: {command.qualified_name} {command.usage or ''}```",
                inline=False,
            )
            .set_footer(
                text=(
                    f"Page 1/1 • Module: " + command.cog_name.lower()
                    if command.cog_name
                    else "N/A"
                ),
            )
        )
        return await self.context.send(embed=embed)
    
    async def send_group_help(self, group: Group):
        embeds = []

        group_permissions = set()
        for cmd in group.commands:
            try:
                if hasattr(cmd, "permissions") and cmd.permissions:  # type: ignore
                    group_permissions.update(cmd.permissions)  # type: ignore
            except (AttributeError, TypeError):
                continue
        
        group_embed = (
            Embed(
                color=COLORS.neutral,
                title=f"Command Group: {group.name}",
                description=group.help or "No description provided",
            )
            .set_author(
                name=self.context.author.name,
                icon_url=self.context.author.display_avatar.url,
            )
            .add_field(
                name="Aliases",
                value=", ".join(group.aliases) if group.aliases else "N/A",
                inline=True,
            )
            .add_field(
                name="Parameters",
                value=", ".join(group.clean_params) if group.clean_params else "N/A",
                inline=True,
            )
            .add_field(
                name="Information",
                value=f"{EMOJIS.WARN} "
                + (", ".join(group_permissions) if group_permissions else "N/A"),
                inline=True,
            )
            .add_field(
                name="Usage",
                value=f"```Syntax: {group.qualified_name} {group.usage or ''}```",
                inline=False,
            )
            .set_footer(
                text=f"Page 1/{len(group.commands) + 1} • Module: {group.cog_name.lower() if group.cog_name else 'N/A'}"
            )
        )
        embeds.append(group_embed)

        for i, command in enumerate(group.commands):
            try:
                permissions = command.permissions  # type: ignore
            except (AttributeError, TypeError):
                permissions = []

            command_embed = (
                Embed(
                    color=COLORS.neutral,
                    title=f"Command: {command.name}",
                    description=command.help or "No description provided",
                )
                .set_author(
                    name=self.context.author.name,
                    icon_url=self.context.author.display_avatar.url,
                )
                .add_field(
                    name="Aliases",
                    value=", ".join(command.aliases) if command.aliases else "N/A",
                    inline=True,
                )
                .add_field(
                    name="Parameters",
                    value=(
                        ", ".join(command.clean_params)
                        if command.clean_params
                        else "N/A"
                    ),
                    inline=True,
                )
                .add_field(
                    name="Information",
                    value=f"{EMOJIS.WARN} "
                    + (", ".join(permissions) if permissions else "N/A"),
                    inline=True,
                )
                .add_field(
                    name="Usage",
                    value=f"```Syntax: {command.qualified_name} {command.usage or ''}```",
                    inline=False,
                )
                .set_footer(
                    text=f"Page {i + 2}/{len(group.commands) + 1} • Module: {command.cog_name.lower() if command.cog_name else 'N/A'}"
                )
            )

            embeds.append(command_embed)
        await self.context.paginate(embeds)



class HelpMenuView(ui.LayoutView):
    COLOR = 0x2B2D31

    def __init__(self, ctx: "Context", modules: Dict[str, List[Command]]):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.modules = modules
        self.add_item(self._container_for("__home__"))

    def home_text(self) -> str:
        bot_user = self.ctx.bot.user
        bot_name = bot_user.name if bot_user else "botname"
        prefix = getattr(self.ctx, "clean_prefix", ".") or "."
        command_count = sum(len(commands) for commands in self.modules.values())
        return (
            f"### **Hey, I'm {bot_name}!**\n"
            "Experience the ultimate Discord bot designed for seamless management, "
            "antinuke, and community engagement.\n"
            f"> `>_` **Prefix** `{prefix}`\n"
            f"> `{{ }}` **Commands** `{command_count}`\n"
            f"> `::: ` **Modules** `{len(self.modules)}`\n\n"
            "Select a category from the **dropdown menu** below to explore my commands."
        )

    def _container_for(self, page: str) -> ui.Container:
        components: List[Any] = []
        if page == "__home__":
            components.append(ui.TextDisplay(self.home_text()))
        else:
            module_commands = self.modules.get(page, [])
            components.append(ui.TextDisplay(f"### **{page}**"))
            command_names = [
                f"`{command.qualified_name}`" for command in module_commands
            ]
            chunks: List[str] = []
            current = ""
            for command_name in command_names:
                candidate = f"{current} {command_name}".strip()
                if current and len(candidate) > 3500:
                    chunks.append(current)
                    current = command_name
                else:
                    current = candidate
            if current:
                chunks.append(current)

            visible_chunks = chunks[:8]
            for chunk in visible_chunks:
                components.append(ui.TextDisplay(chunk))
            if len(chunks) > 8:
                shown = sum(chunk.count("`") // 2 for chunk in visible_chunks)
                components[-1].content += (
                    f"\n*…and {len(module_commands) - shown} more commands*"
                )

        components.append(ui.ActionRow(HelpModuleSelect(self)))
        return ui.Container(*components, accent_colour=self.COLOR)

    def show_page(self, page: str) -> None:
        self.clear_items()
        self.add_item(self._container_for(page))

    async def interaction_check(self, interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Only the person who opened this help menu can use it.",
                ephemeral=True,
            )
            return False
        return True


class HelpModuleSelect(ui.Select):
    def __init__(self, menu: HelpMenuView):
        self.menu = menu
        options = [
            SelectOption(
                label="Home",
                value="__home__",
                description="Return to the help overview.",
            )
        ]
        options.extend(
            SelectOption(
                label=module_name[:100],
                value=module_name[:100],
                description=f"{len(commands)} commands"[:100],
            )
            for module_name, commands in list(menu.modules.items())[:24]
        )
        super().__init__(
            placeholder="Choose a module to explore",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction) -> None:
        selection = self.values[0]
        self.menu.show_page(selection)
        await interaction.response.edit_message(view=self.menu)


class Confirmation(View):
    def __init__(self, ctx: Context, user: Member, reason: str, action: str):
        super().__init__()
        self.ctx = ctx
        self.user = user
        self.reason = reason
        self.action = action
        self.message = None

    async def send_confirmation(self):
        embed = Embed(
            title="",
            description=f"Are you sure you want to {self.action} {self.user.mention if self.user else ''}?",
            color=COLORS.neutral,
        )
        self.message = await self.ctx.send(embed=embed, view=self)

    @ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, button: Button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You cannot confirm this action.", ephemeral=True
            )
            return
        if self.action == "ban" and self.user:
            await self.user.ban(reason=self.reason)
            await self.ctx.approve(f"{self.user.mention} has been **banned**.")
        elif self.action == "kick" and self.user:
            await self.user.kick(reason=self.reason)
            await self.ctx.approve(f"{self.user.mention} has been **kicked**.")

        if self.message:
            await self.message.delete()
        self.stop()

    @ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, button: Button, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You cannot confirm cancel action.", ephemeral=True
            )
            return
        await self.ctx.approve(
            f"{self.action.capitalize()} action has been **cancelled**."
        )
        if self.message:
            await self.message.delete()
        self.stop()
