from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.script import Script, ScriptType, ScriptStatus
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptResponse
from app.services.script_service import ScriptService
from app.core.validation import InputValidator
from app.core.events import event_publisher
from config import settings

router = APIRouter()


@router.get("", response_model=List[ScriptResponse])
async def list_scripts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    script_type: Optional[str] = None,
    status: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """List scripts with filtering"""
    script_service = ScriptService(db)
    scripts = script_service.list_scripts(
        skip=skip,
        limit=limit,
        search=search,
        script_type=script_type,
        status=status
    )
    return scripts


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Get script by ID"""
    script_service = ScriptService(db)
    script = script_service.get_script(script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    return script


@router.post("", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    script_data: ScriptCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create new script"""
    user = request.state.user
    script_service = ScriptService(db)

    is_valid, errors = InputValidator.validate_script_content(
        script_data.content,
        script_data.script_type
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors}
        )

    if script_service.get_script_by_name(script_data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Script with this name already exists"
        )

    script = script_service.create_script(script_data, user['username'])

    await event_publisher.publish(
        "script-events",
        {
            "event_type": "script.created",
            "event_id": str(script.id),
            "service": settings.SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script_id": script.id,
            "script_name": script.name,
            "script_type": script.script_type.value if hasattr(script.script_type, 'value') else script.script_type,
            "created_by": user['username']
        }
    )
    return script


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_data: ScriptUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update script"""
    user = request.state.user
    script_service = ScriptService(db)

    script = script_service.get_script(script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )

    if script_data.content:
        script_type = script_data.script_type or script.script_type
        if hasattr(script_type, 'value'):
            script_type = script_type.value
        is_valid, errors = InputValidator.validate_script_content(
            script_data.content,
            script_type
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors}
            )

    updated_script = script_service.update_script(
        script_id,
        script_data,
        user['username']
    )

    await event_publisher.publish(
        "script-events",
        {
            "event_type": "script.updated",
            "event_id": str(script.id),
            "service": settings.SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script_id": script.id,
            "script_name": script.name,
            "updated_by": user['username'],
            "changes": script_data.dict(exclude_unset=True)
        }
    )
    return updated_script


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete script"""
    user = request.state.user
    script_service = ScriptService(db)

    script = script_service.get_script(script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )

    script_name = script.name
    script_service.delete_script(script_id)

    await event_publisher.publish(
        "script-events",
        {
            "event_type": "script.deleted",
            "event_id": str(script_id),
            "service": settings.SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "script_id": script_id,
            "script_name": script_name,
            "deleted_by": user['username']
        }
    )
    return None