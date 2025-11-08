from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta
import json

from app.db.session import get_db
from app.models.approval import Approval, ApprovalStatus, ApprovalType
from app.schemas.approval import (
    ApprovalCreate, ApprovalResponse, ApprovalDecision, ApprovalRuleCreate
)
from app.services.approval_service import ApprovalService
from app.core.notifications import send_approval_notification

router = APIRouter()

@router.get("", response_model=List[ApprovalResponse])
async def list_approvals(
    status: str = None,
    requester: str = None,
    skip: int = 0,
    limit: int = 100,
    request: Request = None,
    db: Session = Depends(get_db)
):
    user = request.state.user
    service = ApprovalService(db)
    
    return service.list_approvals(
        status=status,
        requester=requester,
        user_role=user['role'],
        skip=skip,
        limit=limit
    )

@router.get("/pending-for-me", response_model=List[ApprovalResponse])
async def get_pending_approvals_for_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get approvals that the current user can approve"""
    user = request.state.user
    service = ApprovalService(db)
    
    return service.get_pending_for_user(user['username'], user['role'])

@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: int, db: Session = Depends(get_db)):
    service = ApprovalService(db)
    approval = service.get_approval(approval_id)
    
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found"
        )
    
    return approval

@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    approval_data: ApprovalCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new approval request"""
    user = request.state.user
    service = ApprovalService(db)
    
    # Check if approval is required
    requires_approval = service.check_approval_required(
        approval_data.approval_type,
        approval_data.resource_type,
        approval_data.resource_id,
        user['role']
    )
    
    if not requires_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This action does not require approval"
        )
    
    # Create approval request
    approval = service.create_approval(approval_data, user['username'])
    
    # Send notification to approvers
    await send_approval_notification(approval)
    
    return approval

@router.post("/{approval_id}/decide", response_model=ApprovalResponse)
async def make_approval_decision(
    approval_id: int,
    decision: ApprovalDecision,
    request: Request,
    db: Session = Depends(get_db)
):
    """Approve or reject an approval request"""
    user = request.state.user
    service = ApprovalService(db)
    
    # Verify user can approve
    approval = service.get_approval(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found"
        )
    
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is already {approval.status}"
        )
    
    # Check if user has permission to approve
    if not service.can_user_approve(approval, user['username'], user['role']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to approve this request"
        )
    
    # Make decision
    approval = service.make_decision(
        approval_id,
        decision.approved,
        user['username'],
        decision.comment
    )
    
    # If approved, trigger the original action
    if approval.status == ApprovalStatus.APPROVED:
        await service.execute_approved_action(approval)
    
    return approval

@router.post("/{approval_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_approval(
    approval_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Cancel an approval request (requester only)"""
    user = request.state.user
    service = ApprovalService(db)
    
    approval = service.get_approval(approval_id)
    
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found"
        )
    
    if approval.requester != user['username']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester can cancel this approval"
        )
    
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approvals can be cancelled"
        )
    
    service.cancel_approval(approval_id)
    return {"message": "Approval cancelled"}

@router.get("/rules", response_model=List[dict])
async def list_approval_rules(
    request: Request,
    db: Session = Depends(get_db)
):
    """List all approval rules (admin only)"""
    user = request.state.user
    
    if user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    service = ApprovalService(db)
    return service.list_rules()

@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_approval_rule(
    rule_data: ApprovalRuleCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new approval rule (admin only)"""
    user = request.state.user
    
    if user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    service = ApprovalService(db)
    return service.create_rule(rule_data, user['username'])