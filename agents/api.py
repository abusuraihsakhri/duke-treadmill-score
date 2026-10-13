"""REST endpoints for the clinical calculator and legacy task-audit subsystem."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictInt, field_validator

from duke import calculate_score
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Duke Treadmill Score API",
    description="Clinical exercise-ECG score calculation and separate legacy task-audit endpoints.",
    version="1.0.0",
)


class DukeRequest(BaseModel):
    exercise_minutes: float = Field(ge=0, allow_inf_nan=False)
    st_deviation_mm: float = Field(ge=0, allow_inf_nan=False)
    angina_index: StrictInt = Field(ge=0, le=2)

    @field_validator('exercise_minutes', 'st_deviation_mm', mode='before')
    @classmethod
    def reject_boolean_measurements(cls, value):
        if isinstance(value, bool):
            raise ValueError('Measurement must be a number, not a boolean')
        return value


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "healthy", "service": "duke-treadmill-score", "version": "1.0.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/duke")
def api_duke(payload: DukeRequest):
    return calculate_score(payload.model_dump())


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    return supervisor.process_task(payload).to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except (SecurityException, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Request failed validation") from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Mounted last: /api/* and /health retain priority over static assets.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"),
                           html=True), name="calculator")
