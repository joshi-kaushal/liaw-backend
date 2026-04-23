import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class ReminderSchema(BaseModel):
    id: str
    type: str = "notification"
    triggerTime: str
    customMinutesBefore: int | None = None
    sent: bool = False


class RecurrencePatternSchema(BaseModel):
    frequency: str
    interval: int
    endDate: str | None = None
    daysOfWeek: list[int] | None = None
    dayOfMonth: int | None = None
    exceptions: list[str] | None = None


class TaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str = ""
    status: str = Field("pending", pattern="^(pending|completed)$")
    completed_at: datetime | None = None
    due_date: date | None = None
    due_time: str | None = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    energy_level: str = Field("medium", pattern="^(low|medium|high)$")
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    priority_override: bool = False
    color: str | None = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    recurrence: dict | None = None  # Using dict for flexibility, or RecurrencePatternSchema
    next_occurrence: date | None = None
    parent_task_id: uuid.UUID | None = None
    instance_date: date | None = None
    reminders: list[dict] = Field(default_factory=list)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    status: str | None = Field(None, pattern="^(pending|completed)$")
    completed_at: datetime | None = None
    due_date: date | None = None
    due_time: str | None = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    energy_level: str | None = Field(None, pattern="^(low|medium|high)$")
    priority: str | None = Field(None, pattern="^(low|medium|high)$")
    priority_override: bool | None = None
    color: str | None = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    recurrence: dict | None = None
    next_occurrence: date | None = None
    parent_task_id: uuid.UUID | None = None
    instance_date: date | None = None
    reminders: list[dict] | None = None

    # Required for optimistic locking
    version: int


class TaskResponse(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class TaskFilterParams(BaseModel):
    status: str | None = None
    priority: str | None = None
    energy_level: str | None = None
    due_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    search: str | None = None
