from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class PromptVersionCreate(BaseModel):
    content: str = Field(..., min_length=1)


class LabelsUpdate(BaseModel):
    labels: list[str]


class PromptVersionOut(BaseModel):
    id: UUID
    prompt_id: UUID
    version: int
    content: str
    content_hash: str
    labels: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptDetailOut(PromptOut):
    versions: list[PromptVersionOut] = []


class DiffOut(BaseModel):
    v1_id: UUID
    v2_id: UUID
    v1_version: int
    v2_version: int
    diff: str
