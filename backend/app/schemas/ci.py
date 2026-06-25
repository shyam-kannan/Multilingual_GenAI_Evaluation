from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CICheckRequest(BaseModel):
    prompt_name: str = Field(..., min_length=1)
    locales: list[str] = Field(
        default=["en-US", "es-MX", "ar-SA", "ja-JP"],
    )
    version_id: Optional[UUID] = None


class RegressionOut(BaseModel):
    locale: str
    metric: str
    baseline: float
    candidate: float
    delta: float


class CICheckResponse(BaseModel):
    ci_run_id: UUID
    passed: bool
    status: str
    regressions: list[RegressionOut]
    details: dict


class CIRunOut(BaseModel):
    id: UUID
    prompt_id: UUID
    candidate_version_id: UUID
    baseline_version_id: Optional[UUID]
    status: str
    regressions: list[dict]
    details: dict
    created_at: str

    model_config = {"from_attributes": True}
