from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from sqlalchemy.engine.url import URL

from barricade.enums import ReportReasonFlag

def get_env_int(key: str, default: int) -> int:
    return int(os.getenv(key, default))

def get_env_float(key: str, default: float) -> float:
    return float(os.getenv(key, default))

def get_env_datetime(key: str, default: datetime | None = None) -> datetime | None:
    value = os.getenv(key)
    if value:
        return datetime.fromisoformat(value).astimezone(tz=timezone.utc)
    else:
        return default

# The path to the .env file
DOTENV_PATH = Path('.env')
load_dotenv(DOTENV_PATH)

# The path pointing to the logs folder
LOGS_FOLDER = Path('logs')
# The format to use for logged events
LOGS_FORMAT = '[%(asctime)s][%(levelname)s][%(module)s.%(funcName)s:%(lineno)s] %(message)s'

if not LOGS_FOLDER.exists():
    print('Adding logs folder:\n', LOGS_FOLDER.absolute())
    LOGS_FOLDER.mkdir()


# The address to forward the web server to
WEB_HOST = os.getenv('WEB_HOST', '127.0.0.1')
WEB_PORT = get_env_int('WEB_PORT', 8080)
# Whether to leave Swagger UI enabled
WEB_DOCS_VISIBLE = os.getenv('WEB_DOCS_VISIBLE', '1').strip().lower() not in ('', '0', 'no', 'off', 'false')

# Load DB parameters from env
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = get_env_int('DB_PORT', 5432)
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')
# Create DB url
DB_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database="barricade",
).render_as_string(hide_password=False)

# Time it takes for web access tokens to expire
ACCESS_TOKEN_EXPIRE_DELTA = timedelta(days=1)

# Discord bot's token
DISCORD_BOT_TOKEN: str = os.getenv('DISCORD_BOT_TOKEN') # type: ignore
if not DISCORD_BOT_TOKEN:
    raise Exception("DISCORD_BOT_TOKEN not set")

# Path to directory with discord.py cogs
DISCORD_COGS_PATH = Path("./barricade/discord/cogs")
# Main Discord guild's ID
DISCORD_GUILD_ID = get_env_int('DISCORD_GUILD_ID', 0)
# ID of the Server Admin role
DISCORD_ADMIN_ROLE_ID = get_env_int('DISCORD_ADMIN_ROLE_ID', 0)
# ID of the Server Owner role
DISCORD_OWNER_ROLE_ID = get_env_int('DISCORD_OWNER_ROLE_ID', 0)
# ID of the PC role
DISCORD_PC_ROLE_ID = get_env_int('DISCORD_PC_ROLE_ID', 0)
# ID of the Console role
DISCORD_CONSOLE_ROLE_ID = get_env_int('DISCORD_CONSOLE_ROLE_ID', 0)
# IDs of the main report channels
DISCORD_PC_REPORTS_CHANNEL_ID = get_env_int('DISCORD_PC_REPORTS_CHANNEL_ID', 0)
DISCORD_CONSOLE_REPORTS_CHANNEL_ID = get_env_int('DISCORD_CONSOLE_REPORTS_CHANNEL_ID', 0)
# ID of the channel to send community create requests to
DISCORD_ENROLL_CHANNEL_ID = get_env_int('DISCORD_ENROLL_CHANNEL_ID', 0)
# ID of the channel to send audit messages to
DISCORD_AUDIT_CHANNEL_ID = get_env_int('DISCORD_AUDIT_CHANNEL_ID', 0)

# ID of the channel to send reports to that are of interest to T17 support
T17_SUPPORT_DISCORD_CHANNEL_ID = get_env_int('T17_SUPPORT_DISCORD_CHANNEL_ID', 0)
# A mask of report reasons. Only reports whose reasons overlaps with this mask are considered for forwarding to T17 support
T17_SUPPORT_REASON_MASK = ReportReasonFlag(get_env_int('T17_SUPPORT_REASON_MASK', 1))
# The amount of responses a report must have before being considered for forwarding to T17 support
T17_SUPPORT_NUM_REQUIRED_RESPONSES = get_env_int('T17_SUPPORT_NUM_REQUIRED_RESPONSES', 20)
# The maximum number of times a report may be rejected by a community to still be considered for forwarding to T17 support
T17_SUPPORT_NUM_ALLOWED_REJECTS = get_env_int('T17_SUPPORT_NUM_ALLOWED_REJECTS', 1)
# A time in ISO 8601 format. If provided, no reports created before this time will be considered for forwarding to T17 support
T17_SUPPORT_CUTOFF_DATE = get_env_datetime('T17_SUPPORT_CUTOFF_DATE')
# The chance for a user to recieve a confirmation prompt when banning a player that qualifies for forwarding to T17 support
T17_SUPPORT_CONFIRMATION_PROMPT_CHANCE = get_env_float('T17_SUPPORT_CONFIRMATION_PROMPT_CHANCE', 0.0)

# How many admins each community is allowed to have (excluding the owner)
MAX_ADMIN_LIMIT = get_env_int('MAX_ADMIN_LIMIT', 3)
# How many integrations each community is allowed to have
MAX_INTEGRATION_LIMIT = get_env_int('MAX_INTEGRATION_LIMIT', 3)

# The URL of the report form. Must end in a "?".
# Note that this cannot just be changed. There's a lot of constants in barricade.urls as well.
REPORT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSedlbl33F6OXaBmaIk6brem79krxSDn_UX9qLymcUOcC7lw-Q/viewform?"
# Time it takes for report tokens (used for submitting reports) to expire
REPORT_TOKEN_EXPIRE_DELTA = timedelta(hours=1)
