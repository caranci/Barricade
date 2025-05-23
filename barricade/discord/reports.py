import discord
from discord.utils import escape_markdown as esc_md
import logging

from barricade import schemas
from barricade.constants import DISCORD_CONSOLE_REPORTS_CHANNEL_ID, DISCORD_PC_REPORTS_CHANNEL_ID, T17_SUPPORT_DISCORD_CHANNEL_ID
from barricade.discord.bot import bot
from barricade.discord.communities import get_admin_name
from barricade.discord.utils import format_url
from barricade.enums import Emojis, Platform, PlayerAlertType, ReportReasonFlag
from barricade.utils import get_player_id_type, PlayerIDType

def get_report_channel(platform: Platform) -> discord.TextChannel:
    if platform == Platform.PC:
        channel_id = DISCORD_PC_REPORTS_CHANNEL_ID
    elif platform == Platform.CONSOLE:
        channel_id = DISCORD_CONSOLE_REPORTS_CHANNEL_ID
    else:
        raise TypeError("Unknown platform %r" % platform)
    
    channel = bot.primary_guild.get_channel(channel_id)
    if not channel:
        raise RuntimeError("%s report channel could not be found" % platform.name)
    elif not isinstance(channel, discord.TextChannel):
        raise RuntimeError("%s report channel is not a text channel" % platform.name)
    return channel

def get_t17_support_forward_channel() -> discord.TextChannel | None:
    if not T17_SUPPORT_DISCORD_CHANNEL_ID:
        return None

    channel = bot.primary_guild.get_channel(T17_SUPPORT_DISCORD_CHANNEL_ID)
    if not channel:
        logging.warning("T17 Support forward channel could not be found")
    elif not isinstance(channel, discord.TextChannel):
        logging.error("T17 Support forward channel is not a text channel")
        channel = None
    return channel

async def get_report_embed(
        report: schemas.ReportWithToken,
        responses: list[schemas.PendingResponse] | None = None,
        stats: dict[int, schemas.ResponseStats] | None = None,
        with_footer: bool = True
) -> discord.Embed:
    embed = discord.Embed(
        colour=discord.Colour.dark_theme(),
        description=esc_md(report.body),
    )
    embed.set_author(
        icon_url=bot.user.avatar.url if bot.user.avatar else None, # type: ignore
        name="\n".join(
            ReportReasonFlag(report.reasons_bitflag).to_list(report.reasons_custom, with_emoji=True)
        )
    )

    if responses and len(responses) != len(report.players):
        raise ValueError("Expected %s responses but got %s" % (len(report.players), len(responses)))

    response = None
    for i, player in enumerate(report.players, 1):
        player_id_type = get_player_id_type(player.player_id)
        is_steam = player_id_type == PlayerIDType.STEAM_64_ID

        if responses:
            response = responses[i - 1] # i starts at 1
        
        name = f"**`{i}.`** {esc_md(player.player_name)}"
        if response:
            if response.banned is True:
                name = f"**`{i}.`**{Emojis.HIGHLIGHT_RED}{esc_md(player.player_name)}"
            elif response.banned is False:
                name = f"**`{i}.`**{Emojis.HIGHLIGHT_GREEN}{esc_md(player.player_name)}"

        if report.token.platform == Platform.PC:
            value = f"{Emojis.STEAM if is_steam else Emojis.EPIC_XBOX} *`{player.player_id}`*"
        else:
            value = f"*`{player.player_id}`*"

        if stats and (stat := stats.get(player.id)):
            num_responses = stat.num_banned + stat.num_rejected
            if num_responses:
                rate = stat.num_banned / num_responses
                if rate >= 0.9:
                    emoji = Emojis.TICK_YES
                elif rate >= 0.7:
                    emoji = Emojis.TICK_MAYBE
                elif rate >= 0.5 or num_responses <= 5:
                    emoji = Emojis.TICK_NO
                else:
                    emoji = "💀"

                value += f"\n{emoji} Banned by **{rate:.0%}** ({stat.num_banned}/{num_responses})"

                reject_reasons = [
                    (reject_reason.value, amount)
                    for reject_reason, amount
                    in stat.reject_reasons.items()
                ]
                reject_reasons.append(("Unbanned", stat.num_rejected - sum(stat.reject_reasons.values())))

                for reject_reason, amount in sorted(reject_reasons, key=lambda x: x[1], reverse=True):
                    if amount > 0:
                        value += f"\n-# {Emojis.ARROW_DOWN_RIGHT}{Emojis.TICK_NO} {amount}x **{reject_reason}**"
        
        if response and response.responded_by:
            value += f"\n-# Responded by **{esc_md(response.responded_by)}** {Emojis.BANNED if response.banned else Emojis.UNBANNED}"

        if player_id_type == PlayerIDType.STEAM_64_ID:
            value += "\n-# " + format_url("View on Steam", f"https://steamcommunity.com/profiles/{player.player_id}")

        bm_rcon_url = player.player.bm_rcon_url
        if bm_rcon_url:
            value += "\n-# " + format_url("View on Battlemetrics", bm_rcon_url)

        embed.add_field(
            name=name,
            value=value,
            inline=True
        )

    if with_footer:
        user = await bot.get_or_fetch_member(report.token.admin_id, strict=False)
        if user and user.avatar:
            avatar_url = user.avatar.url
        else:
            avatar_url = None

        admin_name = await get_admin_name(report.token.admin)

        embed.timestamp = report.created_at
        embed.set_footer(
            text=f"Report by {admin_name} of {report.token.community.name} • {report.token.community.contact_url}",
            icon_url=avatar_url
        )

    return embed

def get_alert_embed(
        reports_urls: list[tuple[schemas.Report, str]],
        player: schemas.PlayerReportRef,
        alert_type: PlayerAlertType,
):
    player_id_type = get_player_id_type(player.player_id)
    is_steam = player_id_type == PlayerIDType.STEAM_64_ID

    title = f"{player.player_name}\n{Emojis.STEAM if is_steam else Emojis.EPIC_XBOX} *`{player.player_id}`*"
    description = []

    if player_id_type == PlayerIDType.STEAM_64_ID:
        description.append(format_url(
            "View on Steam",
            f"https://steamcommunity.com/profiles/{player.player_id}"
        ))

    bm_rcon_url = player.player.bm_rcon_url
    if bm_rcon_url:
        description.append(format_url("View on Battlemetrics", bm_rcon_url))

    if description:
        description.append("")
    
    if alert_type == PlayerAlertType.UNREVIEWED:
        if len(reports_urls) == 1:
            description.append(
                "There is a report against this player that has not yet been reviewed."
                )
        else:
            description.append(
                f"There are {len(reports_urls)} reports against this player that have not yet been reviewed."
            )

    embed = discord.Embed(
        title=title,
        description="\n".join(description),
        colour=discord.Colour.red()
    )

    for report, message_url in reports_urls:
        embed.add_field(
            name="\n".join(
                ReportReasonFlag(report.reasons_bitflag).to_list(report.reasons_custom, with_emoji=True)
            ),
            value=f"{message_url}\n{discord.utils.format_dt(report.created_at, 'R')}"
        )
    
    return embed
