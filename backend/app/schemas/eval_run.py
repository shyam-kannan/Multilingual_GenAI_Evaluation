from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class EvalRunOut(BaseModel):
    id: UUID
    prompt_version_id: UUID
    locale: str
    input_text: str
    llm_output: str
    quality_score: float
    quality_reasoning: str
    hallucination_score: float
    hallucination_reasoning: str
    moderation_passed: bool
    moderation_reasoning: str
    world_readiness_passed: bool
    world_readiness_details: dict
    overall_passed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GatewayRunResponse(BaseModel):
    eval_run_id: UUID
    llm_output: str
    quality_score: float
    hallucination_score: float
    moderation_passed: bool
    world_readiness_passed: bool
    overall_passed: bool
    details: dict
