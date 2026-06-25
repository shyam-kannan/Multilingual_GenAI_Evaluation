from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GatewayRunRequest(BaseModel):
    prompt_name: str = Field(..., min_length=1)
    input: str = Field(..., min_length=1)
    locale: str = Field(..., pattern=r"^(en-US|es-MX|ar-SA|ja-JP)$")
    version_id: Optional[UUID] = None
