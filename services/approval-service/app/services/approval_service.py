from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import json
import httpx

from app.models.approval import Approval, ApprovalStatus, ApprovalRule, ApprovalType
from app.schemas.approval import ApprovalCreate, ApprovalRuleCreate
from config import settings

class ApprovalService:
    def __init__(self, db: Session):
        self.db = db
    
    def list_approvals(
        self,
        status: Optional[str] = None,
        requester: Optional[str] = None,
        user_role: str = "viewer",
        skip: int = 0,
        limit: int = 100
    ) -> List[Approval]:
        query = self.db.query(Approval)
        
        if status:
            query = query.filter(Approval.status == status)
        
        if requester and user_role != "admin":
            query = query.filter(Approval.requester == requester)
        
        return query.order_by(Approval.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_pending_for_user(self, username: str, role: str) -> List[Approval]:
        """Get approvals that user can approve based on role"""
        query = self.db.query(Approval).filter(
            Approval.status == ApprovalStatus.PENDING
        )
        
        # Filter based on approval rules
        approvals = []
        for approval in query.all():
            if self.can_user_approve(approval, username, role):
                approvals.append(approval)
        
        return approvals
    
    def get_approval(self, approval_id: int) -> Optional[Approval]:
        return self.db.query(Approval).filter(Approval.id == approval_id).first()
    
    def check_approval_required(
        self,
        approval_type: str,
        resource_type: str,
        resource_id: int,
        user_role: str
    ) -> bool:
        """Check if approval is required for this action"""
        
        # Admins don't need approval
        if user_role == "admin":
            return False
        
        # Check approval rules
        rules = self.db.query(ApprovalRule).filter(
            ApprovalRule.approval_type == approval_type,
            ApprovalRule.is_active == True
        ).all()
        
        return len(rules) > 0
    
    def create_approval(
        self,
        approval_data: ApprovalCreate,
        username: str
    ) -> Approval:
        """Create new approval request"""
        
        # Get approval rule
        rule = self.db.query(ApprovalRule).filter(
            ApprovalRule.approval_type == approval_data.approval_type,
            ApprovalRule.is_active == True
        ).first()
        
        required_count = rule.required_approvers_count if rule else 1
        
        approval = Approval(
            approval_type=approval_data.approval_type,
            requester=username,
            resource_type=approval_data.resource_type,
            resource_id=approval_data.resource_id,
            action=approval_data.action,
            reason=approval_data.reason,
            metadata=approval_data.metadata,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.DEFAULT_APPROVAL_EXPIRY_HOURS),
            requires_approval_count=required_count
        )
        
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        
        return approval
    
    def can_user_approve(
        self,
        approval: Approval,
        username: str,
        role: str
    ) -> bool:
        """Check if user can approve this request"""
        
        # Can't approve own requests
        if approval.requester == username:
            return False
        
        # Check role requirements
        rule = self.db.query(ApprovalRule).filter(
            ApprovalRule.approval_type == approval.approval_type,
            ApprovalRule.is_active == True
        ).first()
        
        if rule and rule.required_approver_roles:
            allowed_roles = json.loads(rule.required_approver_roles)
            if role not in allowed_roles:
                return False
        
        return True
    
    def make_decision(
        self,
        approval_id: int,
        approved: bool,
        username: str,
        comment: Optional[str] = None
    ) -> Approval:
        """Approve or reject approval request"""
        
        approval = self.get_approval(approval_id)
        
        if approved:
            approval.approval_count += 1
            
            if approval.approval_count >= approval.requires_approval_count:
                approval.status = ApprovalStatus.APPROVED
                approval.approved_at = datetime.now(timezone.utc)
        else:
            approval.status = ApprovalStatus.REJECTED
        
        approval.approver = username
        approval.approval_comment = comment
        
        self.db.commit()
        self.db.refresh(approval)
        
        return approval
    
    async def execute_approved_action(self, approval: Approval):
        """Execute the approved action"""
        
        if approval.resource_type == "script" and approval.action == "execute":
            # Trigger script execution
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.EXECUTION_SERVICE_URL}/api/v1/executions",
                    json={
                        "script_id": approval.resource_id,
                        "parameters": json.loads(approval.metadata) if approval.metadata else {}
                    }
                )
    
    def cancel_approval(self, approval_id: int):
        approval = self.get_approval(approval_id)
        if approval:
            approval.status = ApprovalStatus.CANCELLED
            self.db.commit()
    
    def list_rules(self) -> List[ApprovalRule]:
        return self.db.query(ApprovalRule).filter(ApprovalRule.is_active == True).all()
    
    def create_rule(
        self,
        rule_data: ApprovalRuleCreate,
        username: str
    ) -> ApprovalRule:
        rule = ApprovalRule(
            name=rule_data.name,
            description=rule_data.description,
            approval_type=rule_data.approval_type,
            conditions=rule_data.conditions,
            required_approvers_count=rule_data.required_approvers_count,
            required_approver_roles=rule_data.required_approver_roles,
            created_by=username
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule