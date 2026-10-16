# Deployment shell

The launcher follows the GSA template's platform-port convention. No hosting
account, deployment, authentication, or registry publication is created here.

## Container

```bash
docker build -t bls-escalation-mcp .
docker volume create bls-escalation-data
docker run --rm -p 127.0.0.1:8080:8080 --env-file .env \
  -e BLS_DATABASE_PATH=/data/bls_catalog.db \
  -v bls-escalation-data:/data bls-escalation-mcp
```

The image uses Python 3.12, uv 0.12.18, the locked runtime dependencies, and
a non-root user. `/health` reports process availability, not BLS connectivity
or database readiness; `/version` returns the package version.

## cloud.gov / buildpacks

`manifest.yaml` starts the package through `PYTHONPATH=src` and uses the
generated `requirements.txt`. It deliberately has `no-route: true`: choose
a unique approved route and access controls before serving remotely. The
default `/tmp` database is ephemeral. Set a writable persistent database path
when stored specifications must survive replacement/restarts.

## Databricks and IBM

- Databricks Apps can launch `python -m bls_escalation_mcp.app` with
  `PYTHONPATH=src`, install `requirements.txt`, and inject
  `DATABRICKS_APP_PORT`. Adapt the [upstream Databricks kit](https://github.com/GSA-TTS/mcp-hackathon-template/tree/main/deploy/databricks).
- IBM Code Engine can build this Dockerfile and inject `PORT=8080`.
  Adapt the [upstream IBM kits](https://github.com/GSA-TTS/mcp-hackathon-template/tree/main/deploy/ibm).

The vendor kits are referenced rather than copied with example package names,
accounts, secrets, or unsupported auth assumptions. Platform-specific
deployment and agent registration still require validation in your account.

## Remote-use boundary

The server currently has one operator-supplied BLS key and one shared SQLite
database; it has no per-user credentials, tenant isolation, or HTTP
authentication. Use an approved isolated environment or authenticated gateway
for remote evaluation. Do not expose it as a public multi-user service.
Use one instance with persistent storage; replicas do not share local SQLite.
The operator must also arrange any required outbound BLS network access.

`server.json` is draft identity metadata. Add a real approved `remotes` URL
after deployment, validate against the linked registry schema, and resolve
the project license before publication. It contains no fabricated endpoint.

Regenerate buildpack dependencies after dependency changes:

```bash
uv run --locked poe export-requirements
```
