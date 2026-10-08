# Quickstart

Install Python 3.12 and [uv](https://docs.astral.sh/uv/), then:

```bash
git clone https://github.com/colodnerdata/BLS-basket-mcp-practice.git
cd BLS-basket-mcp-practice
cp .env.example .env
uv sync --locked
uv run --locked python main.py
```

This starts a stdio MCP server, which waits for a client on stdin. It is not
an interactive terminal program. The repository currently requires GitHub
access because it is private. The launcher and BLS settings load `.env`
from the working directory; environment variables take precedence.

For a client supporting stdio server configuration:

```json
{
  "mcpServers": {
    "bls-escalation": {
      "command": "uv",
      "args": ["run", "--locked", "--directory", "/absolute/path/to/BLS-basket-mcp-practice", "python", "main.py"]
    }
  }
}
```

Replace the absolute path. Configure your BLS key in that directory's `.env`
or the client's environment, never in chat. See [BLS setup](docs/bls_api.md).
Restart the server after changing configuration. Existing launches through
`fastmcp.json` and `python -m bls_escalation_mcp.server` remain stdio.

Try asking the client to inspect access status and read `setup://bls-api`,
then explain the methodology. Catalogue search needs seed metadata; this
shell change does not populate a live BLS catalogue. Supplied-value
calculations can run without a BLS key.

For local Streamable HTTP:

```bash
MCP_TRANSPORT=streamable-http uv run --locked python main.py
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/version
```

Connect the MCP client to `http://127.0.0.1:8000/mcp`. Transport precedence is
`DATABRICKS_APP_PORT`, then `PORT`, then `MCP_TRANSPORT`; platform ports bind
to `0.0.0.0`, while explicit local HTTP defaults to loopback.

```bash
uv run --locked poe check
```

For containers and platform configuration, see [deployment](deploy/README.md).
