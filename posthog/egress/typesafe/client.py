"""Bounded HTTP transport for the System One API, ``POST /v1/systemone``.

The request and answer types live in ``posthog.llm.system_one``, because the Go ai-gateway serves
the same API. All callers use the same request path.

USAGE POLICY. TypeSafe's hosted service is approved for experiments only. Read "Usage policy" in this package's
README.md before you add a caller. In short: gate every caller behind a feature flag that reaches
PostHog staff only, and send no customer data. A launch that sends customer data needs an explicit
opt-in from each customer and sign-off from leadership first.
"""

import json
from collections.abc import Mapping
from ipaddress import IPv4Address, IPv6Address
from urllib.parse import urlsplit

from posthog.egress.limiter.policies import Priority
from posthog.egress.typesafe.transport import typesafe_request_async
from posthog.llm.system_one import (
    SYSTEM_ONE_PATH,
    JsonValue,
    Question,
    SystemOneConnectionError,
    SystemOneRequestFailed,
    SystemOneResult,
    build_system_one_body,
    parse_system_one_response,
)

TYPESAFE_API_BASE = "https://api.typesafe.ai"
SYSTEM_ONE_ENDPOINT = SYSTEM_ONE_PATH
MAX_RESPONSE_BYTES = 1_048_576


async def request_system_one(
    *,
    url: str,
    state: JsonValue,
    questions: Mapping[str, Question],
    model: str,
    api_key: str,
    scope: str | None,
    source: str,
    priority: Priority,
    timeout: float,
    pinned_ip: IPv4Address | IPv6Address | None,
    headers: Mapping[str, str] | None = None,
) -> SystemOneResult:
    import aiohttp  # noqa: PLC0415 — keep aiohttp off the Django startup path

    from posthog.security.pinned_aiohttp import PinnedResolver  # noqa: PLC0415 — keep aiohttp off startup

    body = build_system_one_body(state=state, questions=questions, model=model)
    hostname = urlsplit(url).hostname or ""
    connector = aiohttp.TCPConnector(resolver=PinnedResolver(hostname, pinned_ip) if pinned_ip else None)
    # Bound headers and body together so a slow endpoint cannot hold a worker indefinitely.
    client_timeout = aiohttp.ClientTimeout(total=timeout, ceil_threshold=timeout + 1)
    try:
        # nosemgrep: aiohttp-missing-trust-env — a proxy would resolve the customer host outside its validated DNS pin.
        async with aiohttp.ClientSession(
            connector=connector, timeout=client_timeout, auto_decompress=False, trust_env=False
        ) as session:
            response = await typesafe_request_async(
                session,
                "POST",
                url,
                api_key=api_key,
                scope=scope,
                source=source,
                endpoint=SYSTEM_ONE_ENDPOINT,
                priority=priority,
                headers=dict(headers or {}),
                allow_redirects=False,
                json=body,
            )
            async with response:
                content = bytearray()
                if response.status in (200, 422):
                    length = response.headers.get("Content-Length")
                    try:
                        oversized = length is not None and int(length) > MAX_RESPONSE_BYTES
                    except ValueError:
                        oversized = False
                    if oversized or response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise SystemOneRequestFailed("System One response exceeded its limits")
                    async for chunk in response.content.iter_chunked(8192):
                        if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                            raise SystemOneRequestFailed("System One response exceeded its limits")
                        content.extend(chunk)
                if response.status != 200:
                    # A 422 body can echo the state, so keep it out of the exception that gets logged.
                    raise SystemOneRequestFailed(
                        f"System One returned HTTP {response.status}",
                        status_code=response.status,
                        retry_after=response.headers.get("Retry-After"),
                        response_text=content.decode("utf-8", errors="replace"),
                    )
    except (aiohttp.ClientError, TimeoutError) as exc:
        raise SystemOneConnectionError("System One endpoint request failed") from exc
    try:
        payload: object = json.loads(content)
    except (ValueError, UnicodeError) as exc:
        raise SystemOneRequestFailed("System One returned a non-JSON body") from exc
    return parse_system_one_response(payload, questions)
