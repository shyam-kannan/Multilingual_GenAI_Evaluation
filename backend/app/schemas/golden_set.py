from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GoldenExampleCreate(BaseModel):
    prompt_id: UUID
    locale: str = Field(..., pattern=r"^(en-US|es-MX|ar-SA|ja-JP)$")
    input_text: str = Field(..., min_length=1)
    expected_output: Optional[str] = None


class GoldenExampleUpdate(BaseModel):
    input_text: Optional[str] = None
    expected_output: Optional[str] = None
    locale: Optional[str] = Field(None, pattern=r"^(en-US|es-MX|ar-SA|ja-JP)$")


class GoldenExampleOut(BaseModel):
    id: UUID
    prompt_id: UUID
    locale: str
    input_text: str
    expected_output: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
