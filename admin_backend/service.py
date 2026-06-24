"""Business logic for the Aether Glimpse Admin Control Panel."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from admin_backend.config import AdminSettings, get_settings
from admin_backend.dashboard import (
    ENGAGEMENT_SIGNAL_LABELS,
    PROBLEM_CATEGORY_LABELS,
    build_count_buckets,
    calculate_value_inputs,
)
from admin_backend.errors import AdminConfigurationError, AdminConflictError, AdminNotFoundError
from admin_backend.models import (
    AccessLinkView,
    DashboardResponse,
    EnterpriseCreate,
    EnterpriseUpdate,
    EnterpriseView,
    FeedbackPackOption,
    PilotCreate,
    PilotStatus,
    PilotSummary,
    PilotUpdate,
    PilotView,
    TokenStatus,
    TokenType,
    TokenValidationResponse,
)
from admin_backend.repository import AdminPostgresRepository
from backend.feedback import FeedbackConfigError, load_feedback_config


TOKEN_BYTES = 32
TOKEN_PREFIX_LENGTH = 8
AVAILABLE_DASHBOARD_PILOT_STATUSES = {PilotStatus.ACTIVE, PilotStatus.PAUSED}


def hash_access_token(token: str) -> str:
    """Return the stable lookup hash for an external access token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_access_token_value() -> str:
    """Generate a URL-safe external access token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def _clean_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def get_default_service() -> "AdminService":
    settings = get_settings()
    return AdminService(
        repository=AdminPostgresRepository(settings.database_url),
        settings=settings,
    )


class AdminService:
    """Admin control panel operations independent of React."""

    def __init__(self, repository: Any, settings: AdminSettings | None = None) -> None:
        self.repository = repository
        self.settings = settings or get_settings()

    def list_enterprises(self) -> list[EnterpriseView]:
        return [EnterpriseView.model_validate(row) for row in self.repository.list_enterprises()]

    def create_enterprise(self, payload: EnterpriseCreate) -> EnterpriseView:
        row = self.repository.create_enterprise(
            {
                "id": str(uuid.uuid4()),
                "name": payload.name.strip(),
                "status": payload.status.value,
                "notes": payload.notes,
            }
        )
        return EnterpriseView.model_validate(row)

    def get_enterprise(self, enterprise_id: str) -> EnterpriseView:
        row = self.repository.get_enterprise(enterprise_id)
        if row is None:
            raise AdminNotFoundError(f"Enterprise not found: {enterprise_id}")
        return EnterpriseView.model_validate(row)

    def update_enterprise(self, enterprise_id: str, payload: EnterpriseUpdate) -> EnterpriseView:
        current_enterprise = self.get_enterprise(enterprise_id)
        updates = payload.model_dump(exclude_unset=True)
        if "status" in updates and updates["status"] is not None:
            updates["status"] = updates["status"].value
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()

        next_status = updates.get("status")
        if next_status == PilotStatus.CLOSED.value:
            pilots = self.list_pilots_for_enterprise(enterprise_id)
            open_pilots = [
                pilot.name for pilot in pilots
                if pilot.status != PilotStatus.CLOSED
            ]
            if open_pilots:
                raise AdminConflictError(
                    "Enterprise can only be closed when all pilots are closed."
                )

        row = self.repository.update_enterprise(enterprise_id, updates)
        if row is None:
            raise AdminNotFoundError(f"Enterprise not found: {enterprise_id}")
        updated_enterprise = EnterpriseView.model_validate(row)

        if (
            current_enterprise.status.value == "active"
            and updated_enterprise.status.value == "paused"
        ):
            self.repository.update_pilots_status_for_enterprise(
                enterprise_id,
                from_status="active",
                to_status="paused",
            )
        elif (
            current_enterprise.status.value == "paused"
            and updated_enterprise.status.value == "active"
        ):
            self.repository.update_pilots_status_for_enterprise(
                enterprise_id,
                from_status="paused",
                to_status="active",
            )

        return updated_enterprise

    def delete_enterprise(self, enterprise_id: str) -> None:
        enterprise = self.get_enterprise(enterprise_id)
        if enterprise.status.value != "closed":
            raise AdminConflictError("Enterprise can only be deleted when closed.")

        deleted = self.repository.delete_enterprise(enterprise_id)
        if not deleted:
            raise AdminNotFoundError(f"Enterprise not found: {enterprise_id}")

    def list_pilots_for_enterprise(self, enterprise_id: str) -> list[PilotView]:
        self.get_enterprise(enterprise_id)
        return [
            PilotView.model_validate(row)
            for row in self.repository.list_pilots_for_enterprise(enterprise_id)
        ]

    def create_pilot(self, payload: PilotCreate) -> PilotView:
        self.get_enterprise(payload.enterprise_id)
        row = self.repository.create_pilot(
            {
                "id": str(uuid.uuid4()),
                "enterprise_id": payload.enterprise_id,
                "name": payload.name.strip(),
                "status": payload.status.value,
                "start_at": payload.start_at,
                "end_at": payload.end_at,
                "notes": payload.notes,
                "feedback_pack_id": _clean_optional_string(payload.feedback_pack_id),
            }
        )
        return PilotView.model_validate(row)

    def get_pilot(self, pilot_id: str) -> PilotView:
        row = self.repository.get_pilot(pilot_id)
        if row is None:
            raise AdminNotFoundError(f"Pilot not found: {pilot_id}")
        return PilotView.model_validate(row)

    def update_pilot(self, pilot_id: str, payload: PilotUpdate) -> PilotView:
        self.get_pilot(pilot_id)
        updates = payload.model_dump(exclude_unset=True)
        if "status" in updates and updates["status"] is not None:
            updates["status"] = updates["status"].value
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        if "feedback_pack_id" in updates:
            updates["feedback_pack_id"] = _clean_optional_string(updates["feedback_pack_id"])

        row = self.repository.update_pilot(pilot_id, updates)
        if row is None:
            raise AdminNotFoundError(f"Pilot not found: {pilot_id}")
        return PilotView.model_validate(row)

    def delete_pilot(self, pilot_id: str) -> None:
        pilot = self.get_pilot(pilot_id)
        if pilot.status.value != "closed":
            raise AdminConflictError("Pilot can only be deleted when closed.")

        deleted = self.repository.delete_pilot(pilot_id)
        if not deleted:
            raise AdminNotFoundError(f"Pilot not found: {pilot_id}")

    def list_links_for_pilot(self, pilot_id: str) -> list[AccessLinkView]:
        self.get_pilot(pilot_id)
        return [
            self._access_link_from_row(row)
            for row in self.repository.list_latest_tokens_for_pilot(pilot_id)
        ]

    def generate_link(self, pilot_id: str, token_type: TokenType) -> AccessLinkView:
        self.get_pilot(pilot_id)
        existing = self.repository.find_active_token(pilot_id, token_type.value)
        if existing is not None:
            return self._access_link_from_row(existing)

        return self._create_link(pilot_id=pilot_id, token_type=token_type)

    def rotate_link(self, token_id: str) -> AccessLinkView:
        token = self.repository.get_access_token(token_id)
        if token is None:
            raise AdminNotFoundError(f"Token not found: {token_id}")

        self.repository.revoke_access_token(token_id)
        return self._create_link(
            pilot_id=str(token["pilot_id"]),
            token_type=TokenType(str(token["token_type"])),
        )

    def revoke_link(self, token_id: str) -> AccessLinkView:
        token = self.repository.revoke_access_token(token_id)
        if token is None:
            raise AdminNotFoundError(f"Token not found: {token_id}")
        return self._access_link_from_row(token)

    def validate_token(self, token: str, token_type: TokenType) -> TokenValidationResponse:
        token_hash = hash_access_token(token)
        row = self.repository.find_token_by_hash(token_hash)
        if row is None:
            return TokenValidationResponse(valid=False, reason="not_found")

        resolved_type = TokenType(str(row["token_type"]))
        if resolved_type != token_type:
            return TokenValidationResponse(valid=False, reason="wrong_token_type")

        status = TokenStatus(str(row["status"]))
        if status != TokenStatus.ACTIVE:
            return TokenValidationResponse(valid=False, reason=status.value)

        expires_at = row.get("expires_at")
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            return TokenValidationResponse(valid=False, reason="expired")

        self.repository.mark_token_used(str(row["id"]))
        return TokenValidationResponse(
            valid=True,
            pilot_id=str(row["pilot_id"]),
            token_type=resolved_type,
        )

    def get_pilot_summary(self, pilot_id: str) -> PilotSummary:
        pilot = self.get_pilot(pilot_id)
        counts = self.repository.get_pilot_summary_counts(pilot_id)
        links = self.list_links_for_pilot(pilot_id)
        return PilotSummary(
            pilot_id=pilot_id,
            pilot_status=PilotStatus(pilot.status.value),
            sessions_count=int(counts.get("sessions_count") or 0),
            last_activity_at=counts.get("last_activity_at"),
            feedback_records_count=int(counts.get("feedback_records_count") or 0),
            link_statuses={link.token_type: link.status for link in links},
        )

    def list_feedback_pack_options(self) -> list[FeedbackPackOption]:
        try:
            config = load_feedback_config()
        except FeedbackConfigError as exc:
            raise AdminConfigurationError(str(exc)) from exc

        return [
            FeedbackPackOption(id=pack_id, label=pack.label, title=pack.title)
            for pack_id, pack in config.feedback_packs.items()
        ]

    def get_dashboard_data(self, token: str) -> DashboardResponse:
        token_value = token.strip()
        if not token_value:
            return _unavailable_dashboard()

        row = self.repository.find_dashboard_token_context(hash_access_token(token_value))
        if row is None:
            return _unavailable_dashboard()

        try:
            token_status = TokenStatus(str(row["token_status"]))
        except ValueError:
            return _unavailable_dashboard()
        if token_status != TokenStatus.ACTIVE:
            return _unavailable_dashboard()

        if _is_expired(row.get("token_expires_at")):
            return _unavailable_dashboard()

        try:
            pilot_status = PilotStatus(str(row["pilot_status"]))
        except ValueError:
            return _unavailable_dashboard()
        if pilot_status not in AVAILABLE_DASHBOARD_PILOT_STATUSES:
            return _unavailable_dashboard()

        pilot_id = str(row["pilot_id"])
        self.repository.mark_token_used(str(row["token_id"]))

        problem_counts = self.repository.get_problem_category_counts(pilot_id)
        engagement_counts = self.repository.get_engagement_signal_counts(pilot_id)
        feedback_responses = self.repository.list_feedback_responses_for_pilot(pilot_id)

        return DashboardResponse(
            available=True,
            enterprise_name=str(row["enterprise_name"]),
            pilot_name=str(row["pilot_name"]),
            pilot_status=pilot_status,
            problem_categories=build_count_buckets(
                problem_counts,
                PROBLEM_CATEGORY_LABELS,
            ),
            engagement_signals=build_count_buckets(
                engagement_counts,
                ENGAGEMENT_SIGNAL_LABELS,
            ),
            value_unlocked=calculate_value_inputs(feedback_responses),
        )

    def _create_link(self, *, pilot_id: str, token_type: TokenType) -> AccessLinkView:
        token = generate_access_token_value()
        row = self.repository.create_access_token(
            {
                "id": str(uuid.uuid4()),
                "pilot_id": pilot_id,
                "token_type": token_type.value,
                "token_hash": hash_access_token(token),
                "token_recoverable": token,
                "token_prefix": token[:TOKEN_PREFIX_LENGTH],
                "status": TokenStatus.ACTIVE.value,
                "expires_at": None,
            }
        )
        return self._access_link_from_row(row)

    def _access_link_from_row(self, row: dict[str, Any]) -> AccessLinkView:
        token_type = TokenType(str(row["token_type"]))
        status = TokenStatus(str(row["status"]))
        full_access_link = None
        if status == TokenStatus.ACTIVE:
            full_access_link = self._build_full_access_link(
                token_type=token_type,
                token=str(row["token_recoverable"]),
            )

        return AccessLinkView(
            token_id=str(row["id"]),
            pilot_id=str(row["pilot_id"]),
            token_type=token_type,
            status=status,
            full_access_link=full_access_link,
            token_prefix=str(row["token_prefix"]),
            created_at=row["created_at"],
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            revoked_at=row.get("revoked_at"),
        )

    def _build_full_access_link(self, *, token_type: TokenType, token: str) -> str:
        template = (
            self.settings.glimpse_access_url_template
            if token_type == TokenType.GLIMPSE_APP
            else self.settings.dashboard_access_url_template
        )
        if self.settings.require_configured_url_templates and _is_local_url_template(template):
            env_var_name = (
                "GLIMPSE_ACCESS_URL_TEMPLATE"
                if token_type == TokenType.GLIMPSE_APP
                else "DASHBOARD_ACCESS_URL_TEMPLATE"
            )
            raise AdminConfigurationError(
                f"{env_var_name} must be configured for {self.settings.environment_name}."
            )
        if "{token}" not in template:
            raise AdminConfigurationError(
                f"{token_type.value} access URL template must include {{token}}."
            )

        return template.replace("{token}", quote(token, safe=""))


def _is_local_url_template(template: str) -> bool:
    normalized = template.strip().lower()
    return (
        normalized.startswith("http://localhost")
        or normalized.startswith("http://127.0.0.1")
        or normalized.startswith("http://0.0.0.0")
    )


def _is_expired(expires_at: Any) -> bool:
    if expires_at is None:
        return False

    if not isinstance(expires_at, datetime):
        return False

    comparable = expires_at
    if comparable.tzinfo is None:
        comparable = comparable.replace(tzinfo=timezone.utc)

    return comparable <= datetime.now(timezone.utc)


def _unavailable_dashboard() -> DashboardResponse:
    return DashboardResponse(available=False)
