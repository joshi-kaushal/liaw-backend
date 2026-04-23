import uuid
from datetime import datetime

from pydantic import BaseModel
from app.schemas.task import TaskResponse


class SyncPullResponse(BaseModel):
    tasks: list[TaskResponse]
    sync_timestamp: datetime


class SyncChange(BaseModel):
    id: uuid.UUID
    task_data: dict  # Full task data from the client
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
