from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

from fastmcp import Context
from fastmcp.exceptions import ToolError

from bls_escalation_mcp.exceptions import BLSEscalationError
from bls_escalation_mcp.lifespan import Services


def get_services(ctx: Context) -> Services:
    """Get lifespan dependencies; Context is hidden from MCP inputs."""
    return cast(Services, ctx.lifespan_context["services"])


@contextmanager
def domain_errors() -> Iterator[None]:
    """Translate domain failures; leave unexpected errors masked."""
    try:
        yield
    except BLSEscalationError as exc:
        raise ToolError(str(exc)) from exc
