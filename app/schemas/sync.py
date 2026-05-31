import uuid
from datetime import datetime

from pydantic import BaseModel
from app.schemas.task import TaskCreate, TaskResponse


class SyncPullResponse(BaseModel):
    tasks: list[TaskResponse]
    sync_timestamp: datetime


class SyncTaskData(TaskCreate):
    # Sync carries soft-deletes; TaskCreate doesn't expose deleted_at.
    # Inherits TaskCreate's typed fields so Pydantic coerces ISO strings
    # into datetime/date and rejects malformed JSONB payloads.
    deleted_at: datetime | None = None


class SyncChange(BaseModel):
    id: uuid.UUID
    task_data: SyncTaskData  # Full task snapshot from the client (last-write-wins)
    client_version: int


class SyncPushRequest(BaseModel):
    changes: list[SyncChange]


class SyncResult(BaseModel):
    id: uuid.UUID
    status: str  # "accepted" | "conflict" | "error"
    server_task: TaskResponse | None = None
    error_message: str | None = None


class SyncPushResponse(BaseModel):
    results: list[SyncResult]
    sync_timestamp: datetime
