"""HTTP and service models for the separate admin backend."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EnterpriseStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class PilotStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class TokenType(str, Enum):
    GLIMPSE_APP = "glimpse_app"
    DASHBOARD = "dashboard"


class TokenStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class EnterpriseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    status: EnterpriseStatus = EnterpriseStatus.ACTIVE
    notes: str = ""


class EnterpriseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: EnterpriseStatus | None = None
    notes: str | None = None


class EnterpriseView(BaseModel):
    id: str
    name: str
    status: EnterpriseStatus
    notes: str
    created_at: datetime
    updated_at: datetime


class PilotCreate(BaseModel):
    enterprise_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    status: PilotStatus = PilotStatus.DRAFT
    start_at: datetime | None = None
    end_at: datetime | None = None
    notes: str = ""
    feedback_pack_id: str | None = None


class PilotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: PilotStatus | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    notes: str | None = None
    feedback_pack_id: str | None = None


class PilotView(BaseModel):
    id: str
    enterprise_id: str
    name: str
    status: PilotStatus
    start_at: datetime | None = None
    end_at: datetime | None = None
    notes: str
    feedback_pack_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AccessLinkView(BaseModel):
    token_id: str
    pilot_id: str
    token_type: TokenType
    status: TokenStatus
    full_access_link: str | None = None
    token_prefix: str
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class PilotSummary(BaseModel):
    pilot_id: str
    pilot_status: PilotStatus
    sessions_count: int = 0
    last_activity_at: datetime | None = None
    feedback_records_count: int = 0
    link_statuses: dict[TokenType, TokenStatus] = Field(default_factory=dict)


class TokenValidationRequest(BaseModel):
    token: str = Field(min_length=1)
    token_type: TokenType


class TokenValidationResponse(BaseModel):
    valid: bool
    pilot_id: str | None = None
    token_type: TokenType | None = None
    reason: str | None = None


class FeedbackPackOption(BaseModel):
    id: str
    label: str
    title: str


class DashboardCountBucket(BaseModel):
    value: str
    label: str
    count: int = 0


class DashboardValueInputs(BaseModel):
    monthly_minutes: float = 0.0
    qualifying_responses_count: int = 0
    flag_to_organisation: dict[str, int] = Field(
        default_factory=lambda: {"yes_count": 0, "no_count": 0}
    )


class DashboardResponse(BaseModel):
    available: bool
    enterprise_name: str | None = None
    pilot_name: str | None = None
    pilot_status: PilotStatus | None = None
    problem_categories: list[DashboardCountBucket] = Field(default_factory=list)
    engagement_signals: list[DashboardCountBucket] = Field(default_factory=list)
    value_unlocked: DashboardValueInputs = Field(default_factory=DashboardValueInputs)


class DeleteResponse(BaseModel):
    status: str = "deleted"
    id: str
