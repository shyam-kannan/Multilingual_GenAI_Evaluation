import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.uuid_type import CompatibleUUID


class GoldenExample(Base):
    __tablename__ = "golden_examples"

    id: Mapped[uuid.UUID] = mapped_column(
        CompatibleUUID, primary_key=True, default=uuid.uuid4
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        CompatibleUUID, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    prompt = relationship("Prompt")
