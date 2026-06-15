"""FastAPI routes for the separate admin backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from admin_backend.errors import AdminConfigurationError, AdminNotFoundError
from admin_backend.models import (
    AccessLinkView,
    EnterpriseCreate,
    EnterpriseUpdate,
    EnterpriseView,
    PilotCreate,
    PilotSummary,
    PilotUpdate,
    PilotView,
    TokenType,
    TokenValidationRequest,
    TokenValidationResponse,
)
from admin_backend.security import require_admin_auth
from admin_backend.service import AdminService, get_default_service


router = APIRouter()


def get_service() -> AdminService:
    return get_default_service()


def _raise_http_error(exc: Exception) -> None:
    if isinstance(exc, AdminNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if isinstance(exc, AdminConfigurationError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raise HTTPException(status_code=500, detail="Admin operation failed.") from exc


@router.get("/admin/health")
def admin_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/admin/enterprises",
    response_model=list[EnterpriseView],
    dependencies=[Depends(require_admin_auth)],
)
def list_enterprises(service: AdminService = Depends(get_service)) -> list[EnterpriseView]:
    try:
        return service.list_enterprises()
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/admin/enterprises",
    response_model=EnterpriseView,
    dependencies=[Depends(require_admin_auth)],
)
def create_enterprise(
    payload: EnterpriseCreate,
    service: AdminService = Depends(get_service),
) -> EnterpriseView:
    try:
        return service.create_enterprise(payload)
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/admin/enterprises/{enterprise_id}",
    response_model=EnterpriseView,
    dependencies=[Depends(require_admin_auth)],
)
def get_enterprise(
    enterprise_id: str,
    service: AdminService = Depends(get_service),
) -> EnterpriseView:
    try:
        return service.get_enterprise(enterprise_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.patch(
    "/admin/enterprises/{enterprise_id}",
    response_model=EnterpriseView,
    dependencies=[Depends(require_admin_auth)],
)
def update_enterprise(
    enterprise_id: str,
    payload: EnterpriseUpdate,
    service: AdminService = Depends(get_service),
) -> EnterpriseView:
    try:
        return service.update_enterprise(enterprise_id, payload)
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/admin/enterprises/{enterprise_id}/pilots",
    response_model=list[PilotView],
    dependencies=[Depends(require_admin_auth)],
)
def list_pilots_for_enterprise(
    enterprise_id: str,
    service: AdminService = Depends(get_service),
) -> list[PilotView]:
    try:
        return service.list_pilots_for_enterprise(enterprise_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/admin/pilots",
    response_model=PilotView,
    dependencies=[Depends(require_admin_auth)],
)
def create_pilot(payload: PilotCreate, service: AdminService = Depends(get_service)) -> PilotView:
    try:
        return service.create_pilot(payload)
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/admin/pilots/{pilot_id}",
    response_model=PilotView,
    dependencies=[Depends(require_admin_auth)],
)
def get_pilot(pilot_id: str, service: AdminService = Depends(get_service)) -> PilotView:
    try:
        return service.get_pilot(pilot_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.patch(
    "/admin/pilots/{pilot_id}",
    response_model=PilotView,
    dependencies=[Depends(require_admin_auth)],
)
def update_pilot(
    pilot_id: str,
    payload: PilotUpdate,
    service: AdminService = Depends(get_service),
) -> PilotView:
    try:
        return service.update_pilot(pilot_id, payload)
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/admin/pilots/{pilot_id}/summary",
    response_model=PilotSummary,
    dependencies=[Depends(require_admin_auth)],
)
def get_pilot_summary(
    pilot_id: str,
    service: AdminService = Depends(get_service),
) -> PilotSummary:
    try:
        return service.get_pilot_summary(pilot_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.get(
    "/admin/pilots/{pilot_id}/links",
    response_model=list[AccessLinkView],
    dependencies=[Depends(require_admin_auth)],
)
def list_links_for_pilot(
    pilot_id: str,
    service: AdminService = Depends(get_service),
) -> list[AccessLinkView]:
    try:
        return service.list_links_for_pilot(pilot_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/admin/pilots/{pilot_id}/links/glimpse",
    response_model=AccessLinkView,
    dependencies=[Depends(require_admin_auth)],
)
def generate_glimpse_link(
    pilot_id: str,
    service: AdminService = Depends(get_service),
) -> AccessLinkView:
    try:
        return service.generate_link(pilot_id, TokenType.GLIMPSE_APP)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/admin/pilots/{pilot_id}/links/dashboard",
    response_model=AccessLinkView,
    dependencies=[Depends(require_admin_auth)],
)
def generate_dashboard_link(
    pilot_id: str,
    service: AdminService = Depends(get_service),
) -> AccessLinkView:
    try:
        return service.generate_link(pilot_id, TokenType.DASHBOARD)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/admin/tokens/{token_id}/rotate",
    response_model=AccessLinkView,
    dependencies=[Depends(require_admin_auth)],
)
def rotate_token(token_id: str, service: AdminService = Depends(get_service)) -> AccessLinkView:
    try:
        return service.rotate_link(token_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post(
    "/admin/tokens/{token_id}/revoke",
    response_model=AccessLinkView,
    dependencies=[Depends(require_admin_auth)],
)
def revoke_token(token_id: str, service: AdminService = Depends(get_service)) -> AccessLinkView:
    try:
        return service.revoke_link(token_id)
    except Exception as exc:
        _raise_http_error(exc)


@router.post("/access/validate", response_model=TokenValidationResponse)
def validate_access_token(
    payload: TokenValidationRequest,
    service: AdminService = Depends(get_service),
) -> TokenValidationResponse:
    try:
        return service.validate_token(payload.token, payload.token_type)
    except Exception as exc:
        _raise_http_error(exc)

