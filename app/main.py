from typing import Literal

import httpx
import psycopg
from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.config import get_settings
from app.web.routes import router as t13_router

app = FastAPI(title="AI PEL Runtime Policy Enforcement Gate")
app.include_router(t13_router)

StatusValue = Literal["ok", "fail"]


class HealthResponse(BaseModel):
    app: Literal["ok"]
    opa: StatusValue
    db: StatusValue


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    """Serve a simple placeholder page for the T01 scaffold."""

    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>AI PEL</title>
      </head>
      <body>
        <main>
          <h1>Runtime Policy Enforcement Gate</h1>
          <p>Placeholder page for the assurance demo scaffold.</p>
          <p><a href="/health">Check service health</a></p>
        </main>
      </body>
    </html>
    """


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
