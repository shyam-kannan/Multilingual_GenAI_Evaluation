import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("prompt_versions.id"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    llm_output: Mapped[str] = mapped_column(Text, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    quality_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    hallucination_score: Mapped[float] = mapped_column(Float, nullable=False)
    hallucination_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    moderation_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    moderation_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    world_readiness_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    world_readiness_details: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    prompt_version = relationship("PromptVersion")
