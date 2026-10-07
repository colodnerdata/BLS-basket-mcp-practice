# GSA MCP Hackathon template alignment

Compared with [GSA-TTS/mcp-hackathon-template](https://github.com/GSA-TTS/mcp-hackathon-template/tree/33428e31d91e7b08fd1b019455fa12bd4da57a4c)
on 2026-10-07. This project adopts its shell conventions without replacing
the existing BLS implementation with the example server.

| Template element | BLS project mapping |
| --- | --- |
| `main.py`, `app.py` | Thin launcher, stdio by default, platform-port HTTP |
| `config.py`, `.env.example` | BLS `Settings` plus transport-only `LaunchSettings`; `.env` support |
| HTTP `/health`, `/version` | `routes.py`, registered by the existing server factory |
| `Dockerfile`, `.dockerignore` | Locked Python 3.12 runtime and non-root container |
| `requirements.txt` | Runtime export from `uv.lock` for buildpacks |
| `manifest.yaml` | cloud.gov draft with no public route |
| `server.json` | Draft identity, no invented published package or remote URL |
| `QUICKSTART.md`, `SECURITY.md` | Project-specific connection and security guidance |
| `deploy/` | Container/buildpack instructions and links to vendor kits |
| `eval/` | Entry point to the existing planned M5 eval work |
| `tools/`, `resources/`, `models.py`, `utils.py` | Existing typed MCP adapters, model package, clients/services/repositories |
| `prompts/` | Deferred until a concrete reusable prompt is designed |
| `.agents/skills/` | Not vendored; canonical instructions remain `AGENTS.md` |
| `LICENSE` | Owner decision remains open; template MIT license is not assigned to this project |
| CI | Existing locked lint, format, mypy, and test task retained |

Keep the server factory and lifespan ownership. Group related tools by domain
rather than splitting every handler simply to match filenames. Template
deployment scripts and agent skills are optional starter aids, not a reason
to replace reviewed project conventions. This mapping does not certify
hackathon eligibility, deployment readiness, or registry acceptance.
