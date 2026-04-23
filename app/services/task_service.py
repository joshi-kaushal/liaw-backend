import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilterParams


async def get_tasks(
    db: AsyncSession, user_id: uuid.UUID, filters: TaskFilterParams
) -> Sequence[Task]:
    """Get all tasks for a user, optionally filtered."""
    stmt = select(Task).where(Task.user_id == user_id, Task.deleted_at.is_(None))

    if filters.status:
        stmt = stmt.where(Task.status == filters.status)
    if filters.priority:
        stmt = stmt.where(Task.priority == filters.priority)
    if filters.energy_level:
        stmt = stmt.where(Task.energy_level == filters.energy_level)
    if filters.due_date:
        stmt = stmt.where(Task.due_date == filters.due_date)
    if filters.start_date:
        stmt = stmt.where(Task.due_date >= filters.start_date)
    if filters.end_date:
        stmt = stmt.where(Task.due_date <= filters.end_date)
    if filters.search:
        search_term = f"%{filters.search}%"
        stmt = stmt.where(
            (Task.title.ilike(search_term)) | (Task.description.ilike(search_term))
        )

    stmt = stmt.order_by(Task.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_task(db: AsyncSession, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    """Get a single task by ID."""
    stmt = select(Task).where(
        Task.id == task_id, Task.user_id == user_id, Task.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


async def create_task(
    db: AsyncSession, user_id: uuid.UUID, task_in: TaskCreate
) -> Task:
    """Create a new task."""
    task = Task(
        **task_in.model_dump(),
        user_id=user_id,
        version=1,
    )
    db.add(task)
    await db.flush()
    return task


async def update_task(
    db: AsyncSession, user_id: uuid.UUID, task_id: uuid.UUID, task_in: TaskUpdate
) -> Task:
    """Update a task with optimistic locking (version check)."""
    task = await get_task(db, user_id, task_id)

    if task_in.version != task.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version conflict. Server version is {task.version}",
        )

    update_data = task_in.model_dump(exclude_unset=True)
    update_data.pop("version", None)

    for field, value in update_data.items():
        setattr(task, field, value)

    task.version += 1
    await db.flush()
    return task


async def delete_task(db: AsyncSession, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    """Soft delete a task."""
    task = await get_task(db, user_id, task_id)
    
    task.deleted_at = datetime.now(timezone.utc)
    task.version += 1
    
    await db.flush()
    return task
