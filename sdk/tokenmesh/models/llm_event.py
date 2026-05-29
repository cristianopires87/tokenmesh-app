from pydantic import BaseModel
from datetime import datetime


class LLMEvent(BaseModel):
    provider: str
    model: str

    tenant_id: str
    project_id: str
    agent_id: str

    input_tokens: int
    output_tokens: int
    total_tokens: int

    estimated_cost: float

    latency_ms: int

    created_at: datetime
