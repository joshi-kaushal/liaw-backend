import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskFilterParams
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=List[TaskResponse],
    summary="Get all tasks",
)
async def get_tasks(
    filters: Annotated[TaskFilterParams, Depends()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await task_service.get_tasks(db, current_user.id, filters)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task",
)
async def get_task(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await task_service.get_task(db, current_user.id, task_id)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
async def create_task(
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await task_service.create_task(db, current_user.id, task_in)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await task_service.update_task(db, current_user.id, task_id, task_in)


@router.delete(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Delete a task (soft delete)",
)
async def delete_task(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await task_service.delete_task(db, current_user.id, task_id)
