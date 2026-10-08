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

For local Streamable HTTP, set these entries in `.env` first:

```dotenv
MCP_TRANSPORT=streamable-http
MCP_HOST=127.0.0.1
MCP_PORT=8000
```

Launch without terminal environment injection:

```bash
uv run --locked poe serve
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
`uv run --locked poe serve`.
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


Expected successful smoke output:

```text
PASS discovery: 11 tools, 3 resources, 1 resource templates
PASS access status (configuration only; key not verified)
PASS setup and methodology resources
PASS calculation: 110 / 100 = 1.1
PASS smoke check complete; no BLS requests or specification writes
```

Discovery counts may grow as components are added. A missing key is acceptable
for this smoke check. `SMOKE_SUPPLIED_VALUES` is a synthetic label, not a BLS
series; the calculation uses supplied values and never retrieves that ID.

If the check fails, confirm HTTP transport in `.env`, restart the server,
check `/health`, verify the port and `/mcp` URL, and inspect the server logs.
The smoke command accepts only local HTTP URLs (localhost, 127.0.0.1, or ::1)
without URL credentials and bypasses system proxies for the local connection.
Run server and smoke in the same environment, such as both inside WSL.
In stdio mode the server waits for a client on stdin; HTTP smoke cannot connect.
Use Ctrl+C to stop the server. A fresh catalogue may be empty, and no prompts
or agent-eval runner are implemented yet.
