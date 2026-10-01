from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

import httpx
from fastmcp import FastMCP

from bls_escalation_mcp.clients.bls import BLSClient
from bls_escalation_mcp.config import Settings
from bls_escalation_mcp.db.connection import initialize_database
from bls_escalation_mcp.repositories.series import SeriesRepository
from bls_escalation_mcp.repositories.specifications import (
    SpecificationRepository,
)
from bls_escalation_mcp.services.access import BLSAccessService
from bls_escalation_mcp.services.calculations import (
    EscalationCalculationService,
)
from bls_escalation_mcp.services.locality import LocalityService
from bls_escalation_mcp.services.observations import ObservationService
from bls_escalation_mcp.services.series_catalogue import SeriesCatalogueService
from bls_escalation_mcp.services.specifications import SpecificationService
from bls_escalation_mcp.services.validation import ValidationService


@dataclass(frozen=True)
class Services:
    """Dependencies owned by one running server, never a module singleton."""

    access: BLSAccessService
    catalogue: SeriesCatalogueService
    observations: ObservationService
    specifications: SpecificationService
    calculations: EscalationCalculationService
    locality: LocalityService
    validation: ValidationService


def create_lifespan(
    settings: Settings,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> Callable[[FastMCP], AbstractAsyncContextManager[dict[str, Services]]]:
    """Initialize once per server run and close HTTP on every exit path."""

    @asynccontextmanager
    async def app_lifespan(
        server: FastMCP,
    ) -> AsyncIterator[dict[str, Services]]:
        initialize_database(settings.database_path)
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, transport=http_transport
        ) as http_client:
            access = BLSAccessService(settings.bls_api_key)
            services = Services(
                access=access,
                catalogue=SeriesCatalogueService(
                    SeriesRepository(settings.database_path)
                ),
                observations=ObservationService(
                    BLSClient(
                        api_key=settings.bls_api_key,
                        http_client=http_client,
                    ),
                    access,
                ),
                specifications=SpecificationService(
                    SpecificationRepository(settings.database_path)
                ),
                calculations=EscalationCalculationService(
                    weight_tolerance=settings.weight_tolerance
                ),
                locality=LocalityService(),
                validation=ValidationService(settings.weight_tolerance),
            )
            yield {"services": services}

    return app_lifespan
