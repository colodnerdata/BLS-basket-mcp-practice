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


## Python HTTP smoke check (no Node.js)

Set `MCP_TRANSPORT=streamable-http` in the ignored local `.env`, then start
`uv run --locked python main.py` (or `poe serve` once that task is available).
In a second terminal in the repository, run:

```bash
uv run --locked poe smoke
# For a different port:
uv run --locked poe smoke --url http://127.0.0.1:8123/mcp
```

The command prints PASS checks for MCP discovery, access status, guidance
resources, and a supplied-value calculation (110 / 100 = 1.1). It makes no
live BLS requests and does not save specifications. It exits nonzero on any
failure and has a 30-second total timeout (`--timeout` overrides it).
Configuration stays in `.env`; no terminal environment injection is needed.
This checks the running HTTP transport, not agent performance or live BLS.
The existing FastMCP Python client provides the connection; Node.js and
Inspector are optional external debugging tools, not project dependencies.
