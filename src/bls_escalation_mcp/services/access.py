from __future__ import annotations

from bls_escalation_mcp.exceptions import BLSAPIError
from bls_escalation_mcp.models.access import BLSAccessStatus, BLSQueryLimits

REGISTRATION_URL = "https://data.bls.gov/registrationEngine/"
SETUP_GUIDE = """# BLS API setup

This local, single-user server requires a BLS registration key for live
observation retrieval. catalog tools and supplied-value calculations work
without one. No automatic anonymous-access fallback is implemented.

1. Open https://data.bls.gov/registrationEngine/.
2. Enter your email address and organization name, and complete the CAPTCHA.
3. Look for email from labstat@bls.gov containing your registration key.
4. Configure BLS_API_KEY in the environment of the process launching this
   server (or the MCP host's protected server environment configuration).
   Do not paste the key into chat, a tool argument, or a committed file.
5. Restart the server, reconnect, and call get_bls_access_status again.

A .env.example file documents settings; the application does not automatically
load .env files. Changing your terminal environment does not change an already
running server or a separately launched MCP host.

Renew BLS registration at least annually. Configuration is not proof that a
key is valid: this status check makes no network request, consumes no BLS
quota, and does not verify credentials. Explicit verification is deferred.

Registered v2 limits: 500 queries/day, 50 series/query, 20 inclusive calendar
years/query, and 50 requests per 10 seconds. Remaining quota is unknown.
Requests above the series/year limits are rejected before HTTP; automatic
splitting, combining, retries, and rate/quota accounting are deferred.

Published unregistered v1 limits: 25 queries/day, 25 series/query,
10 years/query,
and 50 requests per 10 seconds. This server does not implement v1 access.

For a future multi-user hosted deployment, use an authenticated HTTPS setup
page and per-user credential storage. URL-mode elicitation may link to it
when supported; never collect an API key through form-mode elicitation.
The BLS registration page issues a key but does not configure this server.

Limits and registration checked 2026-10-01:
https://www.bls.gov/developers/api_faqs.htm
"""


class BLSAccessService:
    """Expose setup state without returning or remotely verifying a key."""

    def __init__(self, api_key: str | None) -> None:
        self._configured = bool(api_key and api_key.strip())
        self.limits = BLSQueryLimits()

    def status(self) -> BLSAccessStatus:
        return BLSAccessStatus(
            credential_status=(
                "configured_unverified" if self._configured else "missing"
            ),
            access_mode=(
                "registered_v2" if self._configured else "setup_required"
            ),
            limits=self.limits,
            next_action=(
                "Configuration is present but unverified. Request live data "
                "within the published limits; no remaining quota is known."
                if self._configured
                else "Read setup://bls-api, configure BLS_API_KEY outside "
                "chat, restart the server, reconnect, and recheck status."
            ),
        )

    def setup_guide(self) -> str:
        return SETUP_GUIDE

    def require_configured(self) -> None:
        if not self._configured:
            raise BLSAPIError(
                "BLS_API_KEY is not configured. Read setup://bls-api or call "
                "get_bls_access_status for setup instructions. Supply the "
                "key outside chat, restart the server, and reconnect."
            )
