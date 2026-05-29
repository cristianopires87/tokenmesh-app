from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from collector.database import Base


class LLMEventDB(Base):

    __tablename__ = "llm_events"

    id = Column(Integer, primary_key=True, index=True)

    provider = Column(String, index=True)
    model = Column(String, index=True)

    tenant_id = Column(String, index=True)
    project_id = Column(String, index=True)
    agent_id = Column(String, index=True)

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)

    latency_ms = Column(Integer)
    estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
