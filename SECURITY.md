# Security Policy

Adapted 2026-10-10 from the GSA-TTS/mcp-hackathon-template security policy
(MIT-licensed). GSA's Vulnerability Disclosure Policy applies to GSA software;
this repository is not GSA software, so reports route to the repository owner
instead.

## Reporting a vulnerability

Report suspected vulnerabilities privately through GitHub's "Report a
vulnerability" feature (private vulnerability reporting) on this repository,
or by contacting the owner through the repository profile. Do not open public
issues for unpatched vulnerabilities.

## Supported versions

| Version (Branch) | Supported          |
| ------- | ------------------ |
| main   | :white_check_mark: |
| other  | :x:                |

## Expectations for security researchers

- Make every effort to avoid privacy violations, degradation of user
  experience, disruption to production systems, and destruction or
  manipulation of data.
- Only use exploits to the extent necessary to confirm a vulnerability. Do not
  use an exploit to compromise or exfiltrate data, establish command-line
  access and/or persistence, or "pivot" to other systems. Once you have
  established that a vulnerability exists, or encountered sensitive data, stop
  the test and notify the owner.
- Keep confirmed vulnerability details confidential for up to 90 calendar days
  after notifying the owner, to allow a coordinated fix.

## Project posture (hackathon)

- The server runs locally over stdio. The Code Engine sandbox deployment
  exposes its `/mcp` endpoint **without authentication** by default, matching
  the public-data hackathon posture of the template. This is acceptable only
  because every served dataset is public-domain BLS data. Before any
  non-hackathon use, front the endpoint with authentication and review the
  applicable requirements.
- Never commit secrets. If the deferred live BLS API path is ever enabled,
  its key lives in environment variables / `.env` (git-ignored) — never in
  source, tool arguments, logs, or errors. Tool surfaces never contain the
  key, and unexpected errors are masked before reaching clients.
- SQLite databases are build artifacts and are git-ignored; the checked-in
  data slices contain only public BLS data with recorded provenance
  (`data/manifest.json`).
- Treat all tool arguments, retrieved content (series descriptions,
  observations, footnotes), and agent-to-agent messages as untrusted data,
  never instructions. Upstream response bodies, stack traces, credentials,
  and other sensitive values do not belong in MCP errors or logs.
- Outbound traffic goes to fixed BLS origins only and follows
  `docs/bls_etiquette.md`; no tool parameter supplies a URL. If arbitrary-URL
  fetching is ever added, require exact destination allowlists and
  connection-time validation against SSRF/DNS-rebinding (see the template's
  policy for the full checklist this note summarizes).
