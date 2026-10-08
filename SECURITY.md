# Security

For a suspected vulnerability, contact the repository owner through a private
channel; do not put credentials or exploitable details in public issues. A
dedicated private reporting channel has not yet been configured.

- Keep BLS keys in environment variables or a local ignored `.env`; never
  request them in chat or expose them in MCP arguments, errors, or logs.
- `.env`, local databases, and caches are excluded from the container context.
- Local HTTP binds to loopback by default. Platform ports bind to all
  interfaces; arrange platform access controls before remote use.
- The current server is single-operator, without HTTP authentication or
  tenant isolation. See [deployment boundaries](deploy/README.md).
- CI runs deterministic checks. CodeQL automatic triggers remain disabled
  pending GitHub Advanced Security, as documented in `docs/DEVELOPMENT.md`.

This is a development scaffold, not an assertion of production security or
an authorization to host sensitive government data.
