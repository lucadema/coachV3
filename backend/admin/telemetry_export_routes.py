"""Admin route for downloading telemetry exports."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.telemetry.export import (
    TelemetryExportDatabaseError,
    TelemetryExportWorkbookError,
    build_telemetry_export_workbook,
)


router = APIRouter(prefix="/admin/telemetry", tags=["admin"])

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DEFAULT_LIMIT = 5_000
MAX_LIMIT = 20_000


@router.get("/export.xlsx")
def export_telemetry_workbook(
    token: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> Response:
    """Return telemetry data as an Excel workbook."""
    expected_token = os.getenv("TELEMETRY_EXPORT_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Telemetry export is not configured.",
        )

    if token is None or token != expected_token:
        raise HTTPException(status_code=403, detail="Forbidden.")

    database_url = os.getenv("TELEMETRY_DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="Telemetry database is not configured.",
        )

    try:
        workbook_bytes = build_telemetry_export_workbook(
            database_url=database_url,
            limit=limit,
        )
    except TelemetryExportDatabaseError as exc:
        raise HTTPException(
            status_code=500,
            detail="Telemetry export database query failed.",
        ) from exc
    except TelemetryExportWorkbookError as exc:
        raise HTTPException(
            status_code=500,
            detail="Telemetry export workbook generation failed.",
        ) from exc

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"aether-glimpse-telemetry-{timestamp}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return Response(
        content=workbook_bytes,
        media_type=XLSX_CONTENT_TYPE,
        headers=headers,
    )
