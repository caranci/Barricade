from fastapi import FastAPI

from . import admins
from . import auth
from . import communities
from . import reports
from . import web_users

__all__ = (
    "setup_all",
)

def setup_all(app: FastAPI):
    # Setup authentication routes first
    auth.setup(app)

    admins.setup(app)
    communities.setup(app)
    reports.setup(app)
    web_users.setup(app)
