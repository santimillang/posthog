"""Gated, recorded transport for System One requests.

The TypeSafe metric names and budget namespace stay stable for existing dashboards.
Gateway calls use scope=None: their budget belongs to the gateway, not the TypeSafe account.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from posthog.egress.limiter.outbound import get_outbound_rate_limiter
from posthog.egress.limiter.policies import Priority
from posthog.egress.transport.transport import AsyncEgressClient, EgressBudgetExhausted
from posthog.egress.typesafe.limiter import ACCOUNT_SCOPE_ID, typesafe_account_key
from posthog.egress.typesafe.observability import typesafe_egress

if TYPE_CHECKING:
    import aiohttp


class TypeSafeEgressBudgetExhausted(EgressBudgetExhausted):
    """A sheddable System One call exhausted its egress budget before it was sent."""


class TypeSafeClient(AsyncEgressClient):
    observability = typesafe_egress

    def _standard_headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "Accept-Encoding": "identity", "Content-Type": "application/json"}

    async def _consume(self, scope: str, priority: Priority, source: str, url: str) -> bool:
        return await get_outbound_rate_limiter().acquire(typesafe_account_key(scope), priority=priority, source=source)

    def _budget_exhausted_error(self, scope: str) -> TypeSafeEgressBudgetExhausted:
        return TypeSafeEgressBudgetExhausted("TypeSafe egress budget exhausted; degrading", scope=scope)


_typesafe_client = TypeSafeClient()


async def typesafe_request_async(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    api_key: str,
    source: str,
    endpoint: str,
    scope: str | None = ACCOUNT_SCOPE_ID,
    priority: Priority = Priority.NORMAL,
    headers: dict[str, str] | None = None,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    # CRITICAL skips the spend ceiling, so every request with a local budget must be sheddable.
    if scope and priority is Priority.CRITICAL:
        raise ValueError("TypeSafe calls must be sheddable, so use NORMAL or BATCH")
    return await _typesafe_client.request(
        session,
        method,
        url,
        source=source,
        headers={**(headers or {}), **({"Authorization": f"Bearer {api_key}"} if api_key else {})},
        scope=scope,
        priority=priority,
        endpoint=endpoint,
        **kwargs,
    )
