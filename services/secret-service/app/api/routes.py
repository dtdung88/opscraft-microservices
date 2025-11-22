from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.secret import Secret
from app.models.audit import AuditLog, AuditAction
from app.schemas.secret import SecretCreate, SecretUpdate, SecretResponse, AuditLogResponse
from app.services.secret_service import SecretService
from app.core.encryption import EncryptionService

router = APIRouter()


def get_encryption_service():
    return EncryptionService()


@router.get("", response_model=List[SecretResponse])
async def list_secrets(
    skip: int = 0,
    limit: int = 100,
    request: Request = None,
    db: Session = Depends(get_db),
    encryption: EncryptionService = Depends(get_encryption_service)
):
    service = SecretService(db, encryption)
    secrets = service.list_secrets(skip=skip, limit=limit)
    return secrets


@router.get("/stats")
async def get_secret_stats(
    db: Session = Depends(get_db)
):
    """Get secret statistics"""
    from sqlalchemy import func

    total = db.query(func.count(Secret.id)).filter(Secret.is_active == True).scalar()

    return {
        "total_secrets": total
    }


@router.get("/{secret_id}", response_model=SecretResponse)
async def get_secret(
    secret_id: int,
    reveal: bool = False,
    request: Request = None,
    db: Session = Depends(get_db),
    encryption: EncryptionService = Depends(get_encryption_service)
):
    user = request.state.user
    service = SecretService(db, encryption)
    secret = service.get_secret(secret_id, reveal=reveal, user=user['username'])

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    return secret


@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    secret_data: SecretCreate,
    request: Request,
    db: Session = Depends(get_db),
    encryption: EncryptionService = Depends(get_encryption_service)
):
    user = request.state.user
    service = SecretService(db, encryption)
    secret = service.create_secret(secret_data, user['username'])
    return secret


@router.put("/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: int,
    secret_data: SecretUpdate,
    request: Request,
    db: Session = Depends(get_db),
    encryption: EncryptionService = Depends(get_encryption_service)
):
    user = request.state.user
    service = SecretService(db, encryption)
    secret = service.update_secret(secret_id, secret_data, user['username'])

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    return secret


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: int,
    request: Request,
    db: Session = Depends(get_db),
    encryption: EncryptionService = Depends(get_encryption_service)
):
    user = request.state.user
    service = SecretService(db, encryption)
    service.delete_secret(secret_id, user['username'])
    return None


@router.get("/{secret_id}/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    secret_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    encryption: EncryptionService = Depends(get_encryption_service)
):
    service = SecretService(db, encryption)
    logs = service.get_audit_logs(secret_id)
    return logs