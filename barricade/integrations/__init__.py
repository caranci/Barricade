from sqlalchemy import select
from barricade.db import models, session_factory

from barricade.enums import IntegrationType
from barricade.integrations.custom import CustomIntegration
from barricade.integrations.manager import IntegrationManager
from barricade.logger import get_logger
from .integration import Integration

from .battlemetrics import BattlemetricsIntegration
from .crcon import CRCONIntegration

INTEGRATION_TYPES = (
    CRCONIntegration,
    BattlemetricsIntegration,
    CustomIntegration,
)

def type_to_integration(integration_type: IntegrationType) -> type[Integration]:
    return next(
        integration for integration in INTEGRATION_TYPES
        if integration.meta.type == integration_type
    )

async def load_all():
    manager = IntegrationManager()
    async with session_factory() as db:
        stmt = select(models.Integration)
        results = await db.stream_scalars(stmt)
        async for db_config in results:
            try:
                integration_cls = type_to_integration(db_config.integration_type)
                config = integration_cls.meta.config_cls.model_validate(db_config)
                integration = integration_cls(config)
                manager.add(integration)
            except Exception:
                logger = get_logger(db_config.community_id)
                logger.exception("Failed to load integration %r", db_config)
