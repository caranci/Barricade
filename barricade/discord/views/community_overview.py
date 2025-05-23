from discord import ButtonStyle, Color, Embed, HTTPException, Interaction, Member
from discord.ui import TextInput

from barricade import schemas
from barricade.constants import MAX_ADMIN_LIMIT
from barricade.crud.communities import edit_community, get_community_by_id
from barricade.db import session_factory
from barricade.discord import bot
from barricade.discord.communities import get_forward_channel
from barricade.discord.utils import CustomException, Modal, View, CallableButton, get_command_mention
from barricade.enums import Emojis

class CommunityOverviewView(View):
    def __init__(self, community: schemas.Community, user: Member):
        super().__init__(timeout=500)
        self.user = user
        self.set_community(community)        

    def set_community(self, community: schemas.Community):
        self.community = community
        self.admin = next(
            (admin for admin in community.admins if admin.discord_id == self.user.id),
            None
        )
        self.is_owner = community.owner_id == self.user.id
        self.is_admin = self.admin and not self.is_owner

        self.clear_items()
        if self.is_owner:
            self.add_item(CallableButton(
                self.open_edit_modal,
                style=ButtonStyle.blurple,
                label="Edit"
            ))

    async def open_edit_modal(self, interaction: Interaction):
        async with session_factory() as db:
            db_community = await get_community_by_id(db, self.community.id)
            community = schemas.Community.model_validate(db_community)
            self.set_community(community)

            if self.community.owner_id != interaction.user.id:
                raise CustomException("You no longer own this community!")
            
        modal = CommunityEditModal(self)
        await interaction.response.send_modal(modal)
    
    async def submit_edit_modal(self, interaction: Interaction, modal: 'CommunityEditModal'):
        async with session_factory.begin() as db:
            db_community = await get_community_by_id(db, self.community.id)
            if not db_community:
                raise CustomException("You are no longer part of a community!")
            
            community = schemas.Community.model_validate(db_community)
            if community.owner_id != interaction.user.id:
                raise CustomException("You no longer own this community!")

            params = schemas.CommunityEditParams.model_validate(db_community)
            params.name = modal.name.value
            params.tag = modal.tag.value
            params.contact_url = modal.contact_url.value

            await edit_community(db, db_community, params, by=interaction.user) # type: ignore

        self.set_community(community)
        embed = await self.get_embed(interaction)

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    async def get_embed(self, interaction: Interaction):
        if self.community.is_pc and self.community.is_console:
            platform = "PC & Console"
        elif self.community.is_pc:
            platform = "PC"
        elif self.community.is_console:
            platform = "Console"
        else:
            platform = "Unknown ⚠️"

        embed = Embed(
            title=f"{self.community.tag} {self.community.name}",
            color=Color.blurple(),
        )

        channel = get_forward_channel(self.community)
        if channel:
            embed.set_thumbnail(url=channel.guild.icon.url if channel.guild.icon else None)
            
        if self.is_admin or self.is_owner:
            if not self.community.forward_channel_id:
                channel_mention = "⚠️ *No reports channel*"
            elif not channel:
                channel_mention = "⚠️ *Unknown reports channel*"
            else:
                channel_mention = f"🗒️ {channel.mention}"

            embed.add_field(
                name="Details",
                value=f"{channel_mention}\n{Emojis.CONTACT} {self.community.contact_url}",
            )
        else:
            embed.add_field(
                name="Contact",
                value=f"{Emojis.CONTACT} {self.community.contact_url}",
            )
        
        admin_list = []
        for admin in self.community.admins:
            try:
                member = await bot.get_or_fetch_member(admin.discord_id)
                admin_list.append(member.mention)
            except HTTPException:
                admin_list.append(admin.name)
            
            if self.community.owner_id == admin.discord_id:
                admin_list[-1] += f" {Emojis.OWNER}"

        if admin_list:
            embed.add_field(
                name=f"Admins ({len(self.community.admins)}/{MAX_ADMIN_LIMIT + 1})",
                value="\n".join(admin_list),
            )
        else:
            embed.color = Color.default()
            embed.description = "> This community was abandoned!"

        embed.add_field(
            name="Platform",
            value=platform,
        )

        if self.is_admin:
            embed.add_field(
                name="> Available commands (Admin)",
                value=(
                    ">>> -# "
                    + await get_command_mention(interaction.client.tree, "leave-community", guild_only=True) # type: ignore
                    + " - Leave this community"
                ),
                inline=False
            )
        elif self.is_owner:
            embed.add_field(
                name="> Available commands (Owner)",
                value=(
                    ">>> -# "
                    + await get_command_mention(interaction.client.tree, "add-admin", guild_only=True) # type: ignore
                    + " - Add an admin to your community\n-# "
                    + await get_command_mention(interaction.client.tree, "remove-admin", guild_only=True) # type: ignore
                    + " - Remove an admin from your community\n-# "
                    + await get_command_mention(interaction.client.tree, "transfer-ownership", guild_only=True) # type: ignore
                    + " - Transfer ownership to one of your admins"
                ),
                inline=False
            )
        
        return embed

    async def send(self, interaction: Interaction):
        embed = await self.get_embed(interaction)
        
        await interaction.response.send_message(
            embed=embed,
            view=self,
            ephemeral=True
        )


class CommunityBaseModal(Modal):
    # Also used by EnrollModal
    name = TextInput(
        label="Name",
        placeholder='eg. "My Community"',
        min_length=3,
        max_length=32,
    )
    
    tag = TextInput(
        label="Tag",
        placeholder='eg. "[ABC]", "DEF |"',
        min_length=3,
        max_length=8,
    )

    contact_url = TextInput(
        label="Contact URL",
        placeholder='eg. "discord.gg/ABC"',
        min_length=8,
        max_length=64,
    )

class CommunityEditModal(CommunityBaseModal):
    def __init__(self, view: 'CommunityOverviewView'):
        self.view = view
        community = view.community
        super().__init__(title=f"Community: {community.name}")
        self.name.default = community.name
        self.tag.default = community.tag
        self.contact_url.default = community.contact_url
    
    async def on_submit(self, interaction: Interaction):
        await self.view.submit_edit_modal(interaction, self)
