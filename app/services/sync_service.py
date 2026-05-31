import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.sync import SyncChange, SyncResult
from app.schemas.task import TaskResponse


async def pull_changes(
    db: AsyncSession, user_id: uuid.UUID, since: datetime | None
) -> Sequence[Task]:
    """Get all tasks modified since the given timestamp."""
    stmt = select(Task).where(Task.user_id == user_id)
    if since:
        stmt = stmt.where(Task.updated_at > since)
        
    result = await db.execute(stmt)
    return result.scalars().all()


async def process_sync_change(
    db: AsyncSession, user_id: uuid.UUID, change: SyncChange
) -> SyncResult:
    """Process a single sync change from the client."""
    # Find existing task
    stmt = select(Task).where(Task.id == change.id, Task.user_id == user_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        # Task doesn't exist on server, create it.
        # model_dump yields proper datetime/date objects (Pydantic already
        # coerced the client's ISO strings); id/user_id/version are set
        # server-side, so exclude id and let the others be assigned explicitly.
        new_task_data = change.task_data.model_dump(exclude={"id"})

        task = Task(
            id=change.id,
            user_id=user_id,
            version=1,
            **new_task_data
        )
        db.add(task)
        await db.flush()

        return SyncResult(
            id=change.id,
            status="accepted",
            server_task=TaskResponse.model_validate(task)
        )

    # Task exists, check version
    if change.client_version < task.version:
        # Conflict: server version is newer. Server wins.
        return SyncResult(
            id=change.id,
            status="conflict",
            server_task=TaskResponse.model_validate(task)
        )

    # Accept change — full-object replace (sync is last-write-wins on the
    # whole snapshot). Values are already typed by Pydantic.
    update_data = change.task_data.model_dump(exclude={"id"})

    for field, value in update_data.items():
        if hasattr(task, field):
            setattr(task, field, value)

    task.version += 1
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return SyncResult(
        id=change.id,
        status="accepted",
        server_task=TaskResponse.model_validate(task)
    )


async def push_changes(
    db: AsyncSession, user_id: uuid.UUID, changes: list[SyncChange]
) -> list[SyncResult]:
    """Process a batch of sync changes."""
    results = []
    for change in changes:
        try:
            # SAVEPOINT per change: a failed flush rolls back only this
            # change, leaving the outer transaction usable so one bad
            # change can't poison the rest of the batch (or the final commit).
            async with db.begin_nested():
                result = await process_sync_change(db, user_id, change)
            results.append(result)
        except Exception as e:
            results.append(
                SyncResult(
                    id=change.id,
                    status="error",
                    error_message=str(e)
                )
            )
    return results
