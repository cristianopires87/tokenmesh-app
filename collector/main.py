from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query
from sqlalchemy import func

from tokenmesh.pricing.calculator import calculate_cost
from collector.models import LLMEvent
from collector.database import SessionLocal, engine
from collector.db_models import Base, LLMEventDB

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TokenMesh")


def _db():
    return SessionLocal()


def _apply_filters(q, tenant_id, project_id, agent_id):
    if tenant_id:
        q = q.filter(LLMEventDB.tenant_id == tenant_id)
    if project_id:
        q = q.filter(LLMEventDB.project_id == project_id)
    if agent_id:
        q = q.filter(LLMEventDB.agent_id == agent_id)
    return q


# Root / Health

@app.get("/")
def root():
    return {"project": "TokenMesh", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# Ingest

@app.post("/track")
def track(event: LLMEvent):
    db = _db()
    try:
        estimated_cost = calculate_cost(event.model, event.input_tokens, event.output_tokens)
        db_event = LLMEventDB(
            provider=event.provider,
            model=event.model,
            tenant_id=event.tenant_id,
            project_id=event.project_id,
            agent_id=event.agent_id,
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
            latency_ms=event.latency_ms,
            estimated_cost=estimated_cost,
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return {
            "message": "event tracked",
            "event_id": db_event.id,
            "total_tokens": event.input_tokens + event.output_tokens,
        }
    finally:
        db.close()


# Analytics

@app.get("/analytics/summary")
def analytics_summary(
    tenant_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        base = _apply_filters(db.query(LLMEventDB), tenant_id, project_id, agent_id)
        total_requests = base.count()
        total_input = base.with_entities(func.sum(LLMEventDB.input_tokens)).scalar() or 0
        total_output = base.with_entities(func.sum(LLMEventDB.output_tokens)).scalar() or 0
        avg_latency = base.with_entities(func.avg(LLMEventDB.latency_ms)).scalar() or 0
        return {
            "total_requests": total_requests,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "average_latency_ms": round(avg_latency, 2),
        }
    finally:
        db.close()


@app.get("/analytics/costs")
def analytics_costs(
    tenant_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        base = _apply_filters(db.query(LLMEventDB), tenant_id, project_id, agent_id)
        total_cost = base.with_entities(func.sum(LLMEventDB.estimated_cost)).scalar() or 0
        return {"total_estimated_cost": round(total_cost, 6)}
    finally:
        db.close()


@app.get("/analytics/providers")
def analytics_providers(
    tenant_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        base = _apply_filters(db.query(LLMEventDB), tenant_id, project_id, agent_id)
        rows = (
            base.with_entities(
                LLMEventDB.provider,
                func.count(LLMEventDB.id),
                func.sum(LLMEventDB.input_tokens),
                func.sum(LLMEventDB.output_tokens),
                func.sum(LLMEventDB.estimated_cost),
            )
            .group_by(LLMEventDB.provider)
            .all()
        )
        return [
            {
                "provider": provider,
                "requests": requests,
                "input_tokens": input_tokens or 0,
                "output_tokens": output_tokens or 0,
                "total_tokens": (input_tokens or 0) + (output_tokens or 0),
                "estimated_cost": round(estimated_cost or 0, 6),
            }
            for provider, requests, input_tokens, output_tokens, estimated_cost in rows
        ]
    finally:
        db.close()


@app.get("/analytics/agents")
def analytics_agents(
    tenant_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        base = _apply_filters(db.query(LLMEventDB), tenant_id, project_id, None)
        rows = (
            base.with_entities(
                LLMEventDB.agent_id,
                func.count(LLMEventDB.id),
                func.sum(LLMEventDB.input_tokens + LLMEventDB.output_tokens),
                func.sum(LLMEventDB.estimated_cost),
            )
            .group_by(LLMEventDB.agent_id)
            .all()
        )
        return [
            {
                "agent_id": agent_id,
                "requests": requests,
                "total_tokens": total_tokens or 0,
                "total_cost": round(total_cost or 0, 6),
            }
            for agent_id, requests, total_tokens, total_cost in rows
        ]
    finally:
        db.close()


@app.get("/analytics/projects")
def analytics_projects(
    tenant_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        base = _apply_filters(db.query(LLMEventDB), tenant_id, None, None)
        rows = (
            base.with_entities(
                LLMEventDB.project_id,
                func.count(LLMEventDB.id),
                func.sum(LLMEventDB.input_tokens + LLMEventDB.output_tokens),
                func.sum(LLMEventDB.estimated_cost),
            )
            .group_by(LLMEventDB.project_id)
            .all()
        )
        return [
            {
                "project_id": project_id,
                "requests": requests,
                "total_tokens": total_tokens or 0,
                "total_cost": round(total_cost or 0, 6),
            }
            for project_id, requests, total_tokens, total_cost in rows
        ]
    finally:
        db.close()


@app.get("/analytics/models")
def analytics_models(
    tenant_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        base = _apply_filters(db.query(LLMEventDB), tenant_id, project_id, agent_id)
        rows = (
            base.with_entities(
                LLMEventDB.model,
                func.count(LLMEventDB.id),
                func.sum(LLMEventDB.input_tokens + LLMEventDB.output_tokens),
                func.sum(LLMEventDB.estimated_cost),
            )
            .group_by(LLMEventDB.model)
            .all()
        )
        return [
            {
                "model": model,
                "requests": requests,
                "total_tokens": total_tokens or 0,
                "total_cost": round(total_cost or 0, 6),
            }
            for model, requests, total_tokens, total_cost in rows
        ]
    finally:
        db.close()


@app.get("/analytics/timeline")
def analytics_timeline(
    days: int = Query(30, ge=1, le=365),
    tenant_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
):
    db = _db()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        base = _apply_filters(
            db.query(LLMEventDB), tenant_id, project_id, agent_id
        ).filter(LLMEventDB.created_at >= cutoff)
        day_col = func.date(LLMEventDB.created_at)
        rows = (
            base.with_entities(
                day_col.label("day"),
                func.count(LLMEventDB.id).label("requests"),
                func.sum(LLMEventDB.input_tokens + LLMEventDB.output_tokens).label("total_tokens"),
                func.sum(LLMEventDB.estimated_cost).label("total_cost"),
            )
            .group_by(day_col)
            .order_by(day_col)
            .all()
        )
        return [
            {
                "date": str(r.day),
                "requests": r.requests,
                "total_tokens": r.total_tokens or 0,
                "total_cost": round(r.total_cost or 0, 6),
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/analytics/filters")
def analytics_filters():
    db = _db()
    try:
        tenants = sorted(r[0] for r in db.query(LLMEventDB.tenant_id).distinct().all() if r[0])
        projects = sorted(r[0] for r in db.query(LLMEventDB.project_id).distinct().all() if r[0])
        agents = sorted(r[0] for r in db.query(LLMEventDB.agent_id).distinct().all() if r[0])
        return {"tenants": tenants, "projects": projects, "agents": agents}
    finally:
        db.close()
