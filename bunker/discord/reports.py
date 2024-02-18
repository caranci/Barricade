import discord
from discord.utils import escape_markdown as esc_md

from bunker import schemas
from bunker.constants import DISCORD_REPORTS_CHANNEL_ID
from bunker.discord.bot import bot
from bunker.discord.communities import get_admin_name
from bunker.utils import get_player_id_type, PlayerIDType

def get_report_channel():
    return bot.primary_guild.get_channel(DISCORD_REPORTS_CHANNEL_ID)


async def get_report_embed(report: schemas.ReportCreateParams | schemas.ReportWithToken, with_footer: bool = True) -> discord.Embed:
    embed = discord.Embed(
        description="**" + "**\n**".join(report.reasons_bitflag.to_list(report.reasons_custom)) + "**\n" + esc_md(report.body),
        colour=discord.Colour.dark_theme()
    )

    for i, player in enumerate(report.players, 1):
        if isinstance(player, schemas.PlayerReportCreateParams):
            bm_rcon_url = player.bm_rcon_url
        else:
            bm_rcon_url = player.player.bm_rcon_url

        value = f"*`{player.player_id}`*"

        player_id_type = get_player_id_type(player.player_id)
        if player_id_type == PlayerIDType.STEAM_64_ID:
            value += f"\n[**View on Steam** 🡥](https://steamcommunity.com/profiles/{player.player_id})"

        if bm_rcon_url:
            value += f"\n[**View on Battlemetrics** 🡥]({bm_rcon_url})"

        embed.add_field(
            name=f"**`{i}.`** {esc_md(player.player_name)}",
            value=value,
            inline=True
        )

    if with_footer:
        try:
            user = await bot.get_or_fetch_user(report.token.admin_id)
        except discord.NotFound:
            avatar_url = None
        else:
            avatar_url = user.avatar.url

        admin_name = await get_admin_name(report.token.admin)

        embed.set_footer(
            text=f"Report by {admin_name} of {report.token.community.name} • {report.token.community.contact_url}",
            icon_url=avatar_url
        )

    return embed
