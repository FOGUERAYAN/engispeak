"""Service 1 : web-app EngiSpeak (FastAPI + templates Jinja/Tailwind CDN)."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from engispeak import __version__
from engispeak.config import Settings, get_settings
from engispeak.logging_utils import setup_logging
from engispeak.progress import UnknownStepError, summarize, validate_step_id
from engispeak.roadmap import ROADMAP, SESSION_FORMAT, get_week, week_of
from engispeak.storage import (
    ProgressStore,
    ResourceStore,
    build_progress_store,
    build_resource_store,
)
from engispeak.storage.resource_store import ResourceNotFoundError

logger = logging.getLogger("engispeak.web")

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
COOKIE_NAME = "engispeak_student"
STUDENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")


class StepUpdate(BaseModel):
    completed: bool


def normalize_student_id(raw: str) -> str:
    candidate = raw.strip().lower().replace(" ", "-")
    if not STUDENT_ID_RE.match(candidate):
        raise ValueError("Identifiant invalide")
    return candidate


def create_app(
    settings: Settings | None = None,
    progress_store: ProgressStore | None = None,
    resource_store: ResourceStore | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(title="EngiSpeak", version=__version__)
    app.state.settings = settings
    app.state.progress = progress_store or build_progress_store(settings)
    app.state.resources = resource_store or build_resource_store(settings)

    def get_progress_store(request: Request) -> ProgressStore:
        return request.app.state.progress

    def get_resource_store(request: Request) -> ResourceStore:
        return request.app.state.resources

    def current_student(request: Request) -> str | None:
        raw = request.cookies.get(COOKIE_NAME)
        if not raw:
            return None
        try:
            return normalize_student_id(raw)
        except ValueError:
            return None

    # ---------- Monitoring ----------

    @app.get("/health", tags=["monitoring"])
    def health() -> dict:
        """Liveness probe pour le Load Balancer / Azure Monitor."""
        return {"status": "ok", "version": __version__}

    @app.get("/ready", tags=["monitoring"])
    def ready(store: ProgressStore = Depends(get_progress_store)) -> JSONResponse:
        ok = store.ping()
        return JSONResponse(
            {"status": "ready" if ok else "degraded", "database": ok},
            status_code=200 if ok else 503,
        )

    # ---------- Pages HTML ----------

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, store: ProgressStore = Depends(get_progress_store)):
        student = current_student(request)
        if student is None:
            return TEMPLATES.TemplateResponse(request, "login.html", {"error": None})
        summary = summarize(store.get_progress(student))
        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "student": student,
                "summary": summary,
                "roadmap": ROADMAP,
                "session_format": SESSION_FORMAT,
                "done": set(store.get_progress(student)),
            },
        )

    @app.post("/login")
    def login(request: Request, student_id: str = Form(...)):
        try:
            student = normalize_student_id(student_id)
        except ValueError:
            return TEMPLATES.TemplateResponse(
                request,
                "login.html",
                {"error": "Utilise 2 à 32 caractères : lettres, chiffres, point, tiret ou underscore."},
                status_code=400,
            )
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(COOKIE_NAME, student, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 60)
        logger.info("connexion", extra={"student_id": student})
        return response

    @app.post("/logout")
    def logout():
        response = RedirectResponse("/", status_code=303)
        response.delete_cookie(COOKIE_NAME)
        return response

    @app.get("/weeks/{number}", response_class=HTMLResponse)
    def week_page(number: int, request: Request, store: ProgressStore = Depends(get_progress_store)):
        student = current_student(request)
        if student is None:
            return RedirectResponse("/", status_code=303)
        week = get_week(number)
        if week is None:
            raise HTTPException(status_code=404, detail="Semaine introuvable")
        done = set(store.get_progress(student))
        return TEMPLATES.TemplateResponse(
            request,
            "week.html",
            {"student": student, "week": week, "done": done, "roadmap": ROADMAP},
        )

    @app.post("/steps/{step_id}/toggle")
    def toggle_step(step_id: str, request: Request, store: ProgressStore = Depends(get_progress_store)):
        student = current_student(request)
        if student is None:
            return RedirectResponse("/", status_code=303)
        try:
            validate_step_id(step_id)
        except UnknownStepError:
            raise HTTPException(status_code=404, detail="Étape inconnue") from None
        completed = step_id not in store.get_progress(student)
        store.set_step(student, step_id, completed)
        logger.info("etape", extra={"student_id": student, "step_id": step_id, "completed": completed})
        return RedirectResponse(f"/weeks/{week_of(step_id)}#{step_id}", status_code=303)

    @app.get("/resources", response_class=HTMLResponse)
    def resources_page(request: Request, resources: ResourceStore = Depends(get_resource_store)):
        return TEMPLATES.TemplateResponse(
            request,
            "resources.html",
            {
                "student": current_student(request),
                "resources": resources.list_resources(),
                "backend": resources.backend,
            },
        )

    @app.get("/resources/{name}")
    def download_resource(name: str, resources: ResourceStore = Depends(get_resource_store)):
        try:
            data, content_type = resources.read(name)
        except ResourceNotFoundError:
            raise HTTPException(status_code=404, detail="Ressource introuvable") from None
        return Response(
            content=data,
            media_type=content_type,
            headers={"Content-Disposition": f'inline; filename="{name}"'},
        )

    # ---------- API JSON ----------

    @app.get("/api/roadmap", tags=["api"])
    def api_roadmap() -> list[dict]:
        return [
            {
                "week": w.number,
                "level": w.level,
                "themes": w.themes,
                "focus": w.focus,
                "steps": [{"id": s.id, "kind": s.kind, "title": s.title, "talk": s.talk} for s in w.steps],
            }
            for w in ROADMAP
        ]

    @app.get("/api/students/{student_id}/progress", tags=["api"])
    def api_progress(student_id: str, store: ProgressStore = Depends(get_progress_store)) -> dict:
        try:
            student = normalize_student_id(student_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Identifiant invalide") from None
        progress = store.get_progress(student)
        summary = summarize(progress)
        return {
            "student_id": student,
            "completed_steps": sorted(progress),
            "completed": summary.completed,
            "total": summary.total,
            "percent": summary.percent,
            "current_week": summary.current_week,
            "next_step": summary.next_step.id if summary.next_step else None,
        }

    @app.put("/api/students/{student_id}/steps/{step_id}", tags=["api"])
    def api_set_step(
        student_id: str,
        step_id: str,
        body: StepUpdate,
        store: ProgressStore = Depends(get_progress_store),
    ) -> dict:
        try:
            student = normalize_student_id(student_id)
            validate_step_id(step_id)
        except UnknownStepError:
            raise HTTPException(status_code=404, detail="Étape inconnue") from None
        except ValueError:
            raise HTTPException(status_code=422, detail="Identifiant invalide") from None
        store.set_step(student, step_id, body.completed)
        return {"student_id": student, "step_id": step_id, "completed": body.completed}

    return app
