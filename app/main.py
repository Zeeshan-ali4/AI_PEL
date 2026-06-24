from typing import Literal

import httpx
import psycopg
from fastapi import FastAPI, Response, status
from pydantic import BaseModel

from app.config import get_settings
from app.web.routes import router as dashboard_router

app = FastAPI(title="AI PEL Runtime Policy Enforcement Gate")
app.include_router(dashboard_router)

StatusValue = Literal["ok", "fail"]


class HealthResponse(BaseModel):
    app: Literal["ok"]
    opa: StatusValue
    db: StatusValue


@app.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    """Check the application, OPA, and Postgres connectivity."""

    opa_status = _check_opa()
    db_status = _check_db()

    if opa_status != "ok" or db_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(app="ok", opa=opa_status, db=db_status)


def _check_opa() -> StatusValue:
    settings = get_settings()
    try:
        with httpx.Client(timeout=2.0) as client:
            result = client.get(f"{settings.opa_url.rstrip('/')}/health")
            result.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        return "fail"
    return "ok"


def _check_db() -> StatusValue:
    settings = get_settings()
    try:
        with psycopg.connect(
            **settings.postgres_connection_kwargs,
            connect_timeout=2,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except psycopg.Error:
        return "fail"
    return "ok"
