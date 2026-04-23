from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.sync import SyncPullResponse, SyncPushRequest, SyncPushResponse
from app.schemas.task import TaskResponse
from app.services import sync_service

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.get(
    "/pull",
    response_model=SyncPullResponse,
    summary="Pull changes from server",
)
async def pull_changes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    since: datetime | None = Query(None, description="ISO timestamp of last sync"),
):
    tasks = await sync_service.pull_changes(db, current_user.id, since)
    
    return SyncPullResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        sync_timestamp=datetime.now(timezone.utc)
    )


@router.post(
    "/push",
    response_model=SyncPushResponse,
    summary="Push changes to server",
)
async def push_changes(
    body: SyncPushRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    results = await sync_service.push_changes(db, current_user.id, body.changes)
    
    return SyncPushResponse(
        results=results,
        sync_timestamp=datetime.now(timezone.utc)
    )
