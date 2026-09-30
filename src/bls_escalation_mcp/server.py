from __future__ import annotations

from fastmcp import FastMCP

from bls_escalation_mcp.mcp.resources.methodology import (
    composite_index_methodology,
    locality_adjustment_methodology,
)
from bls_escalation_mcp.mcp.resources.series import get_series_resource
from bls_escalation_mcp.mcp.tools.calculations import (
    calculate_component_escalation,
    calculate_index_spec,
)
from bls_escalation_mcp.mcp.tools.discovery import (
    describe_series,
    search_series,
)
from bls_escalation_mcp.mcp.tools.locality import (
    calculate_labor_locality_factor,
)
from bls_escalation_mcp.mcp.tools.observations import get_series_data
from bls_escalation_mcp.mcp.tools.specifications import (
    create_index_spec,
    get_index_spec,
    save_index_spec,
)
from bls_escalation_mcp.mcp.tools.validation import validate_index_spec


def create_server() -> FastMCP:
    mcp = FastMCP("BLS Cost Escalation")

    mcp.tool()(search_series)
    mcp.tool()(describe_series)
    mcp.tool()(get_series_data)
    mcp.tool()(create_index_spec)
    mcp.tool()(save_index_spec)
    mcp.tool()(get_index_spec)
    mcp.tool()(calculate_component_escalation)
    mcp.tool()(calculate_index_spec)
    mcp.tool()(calculate_labor_locality_factor)
    mcp.tool()(validate_index_spec)

    @mcp.resource("bls://series/{series_id}")
    def series_resource(series_id: str):
        return get_series_resource(series_id)

    @mcp.resource("methodology://composite-index")
    def methodology_composite_index_resource():
        return composite_index_methodology()

    @mcp.resource("methodology://locality-adjustment")
    def methodology_locality_resource():
        return locality_adjustment_methodology()

    return mcp


server = create_server()


if __name__ == "__main__":
    server.run()
