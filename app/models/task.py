import uuid
from datetime import datetime, date

from sqlalchemy import (
    String, Boolean, Text, Integer, Date, DateTime,
    ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # 'pending' | 'completed'
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Scheduling
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    due_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # HH:mm

    # Priority & Energy
    energy_level: Mapped[str] = mapped_column(String(10), default="medium")
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    priority_override: Mapped[bool] = mapped_column(Boolean, default=False)

    # Visual
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # #RRGGBB

    # Recurrence (JSONB — matches extension's RecurrencePattern)
    recurrence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    next_occurrence: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Parent/child (for recurring instances + future hierarchy)
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    instance_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Reminders (JSONB array)
    reminders: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Sync
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )  # Soft delete

    # Relationships
    user = relationship("User", back_populates="tasks")
    children = relationship(
        "Task",
        back_populates="parent",
        foreign_keys=[parent_task_id],
    )
    parent = relationship(
        "Task",
        back_populates="children",
        remote_side="Task.id",
        foreign_keys=[parent_task_id],
    )
