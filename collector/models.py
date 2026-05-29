from pydantic import BaseModel


class LLMEvent(BaseModel):
    provider: str
    model: str

    tenant_id: str
    project_id: str
    agent_id: str

    input_tokens: int
    output_tokens: int

    latency_ms: int
