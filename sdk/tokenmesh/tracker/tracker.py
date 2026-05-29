import os
from datetime import datetime, timezone

import httpx

from tokenmesh.models.llm_event import LLMEvent
from tokenmesh.pricing.calculator import calculate_cost


class TokenTracker:

    def __init__(self, collector_url: str = None):
        self.collector_url = (
            collector_url
            or os.getenv("TOKENMESH_COLLECTOR_URL", "http://localhost:8000")
        )

    def track(
        self,
        provider: str,
        model: str,
        tenant_id: str,
        project_id: str,
        agent_id: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
    ) -> LLMEvent:

        event = LLMEvent(
            provider=provider,
            model=model,
            tenant_id=tenant_id,
            project_id=project_id,
            agent_id=agent_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost=calculate_cost(model, input_tokens, output_tokens),
            latency_ms=latency_ms,
            created_at=datetime.now(timezone.utc),
        )

        self._send(event)
        return event

    def _send(self, event: LLMEvent) -> None:
        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(
                    f"{self.collector_url}/track",
                    json=event.model_dump(mode="json"),
                )
        except Exception:
            # Collector unavailable; print locally so no event is silently lost
            print(event.model_dump_json(indent=2))
