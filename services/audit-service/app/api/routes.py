from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import csv
import io

from app.db.session import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse, AuditSearchRequest, AuditStatistics

router = APIRouter()

@router.get("/logs", response_model=List[AuditLogResponse])
async def search_audit_logs(
    user: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    risk_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search audit logs with filters"""
    query = db.query(AuditLog)
    
    if user:
        query = query.filter(AuditLog.username == user)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    if risk_level:
        query = query.filter(AuditLog.risk_level == risk_level)
    
    return query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(log_id: int, db: Session = Depends(get_db)):
    """Get specific audit log entry"""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return log

@router.get("/statistics")
async def get_audit_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get audit statistics"""
    query = db.query(AuditLog)
    
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    
    if not end_date:
        end_date = datetime.now()
    
    query = query.filter(
        and_(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    )
    
    total_events = query.count()
    
    # Events by category
    from sqlalchemy import func
    events_by_category = dict(
        query.with_entities(
            AuditLog.event_category,
            func.count(AuditLog.id)
        ).group_by(AuditLog.event_category).all()
    )
    
    # Events by user
    top_users = query.with_entities(
        AuditLog.username,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.username).order_by(desc('count')).limit(10).all()
    
    # Failed actions
    failed_actions = query.filter(AuditLog.status == 'failure').count()
    
    # High risk events
    high_risk_events = query.filter(AuditLog.risk_level == 'high').count()
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "total_events": total_events,
        "events_by_category": events_by_category,
        "top_users": [{"username": u, "count": c} for u, c in top_users],
        "failed_actions": failed_actions,
        "high_risk_events": high_risk_events,
        "success_rate": ((total_events - failed_actions) / total_events * 100) if total_events > 0 else 0
    }

@router.get("/export/csv")
async def export_audit_logs_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Export audit logs to CSV"""
    from fastapi.responses import StreamingResponse
    
    query = db.query(AuditLog)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    logs = query.order_by(desc(AuditLog.timestamp)).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Timestamp', 'Username', 'Event Type', 'Action',
        'Resource Type', 'Resource ID', 'Status', 'Risk Level', 'IP Address'
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp,
            log.username,
            log.event_type,
            log.action,
            log.resource_type,
            log.resource_id,
            log.status,
            log.risk_level,
            log.ip_address
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )

@router.get("/timeline")
async def get_audit_timeline(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db)
):
    """Get timeline of changes for a resource"""
    logs = db.query(AuditLog).filter(
        and_(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        )
    ).order_by(AuditLog.timestamp).all()
    
    timeline = []
    for log in logs:
        timeline.append({
            "timestamp": log.timestamp,
            "user": log.username,
            "action": log.action,
            "changes": {
                "old": log.old_values,
                "new": log.new_values
            } if log.old_values or log.new_values else None,
            "status": log.status
        })
    
    return {
        "resource": {
            "type": resource_type,
            "id": resource_id
        },
        "timeline": timeline
    }

@router.get("/compliance/report")
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """Generate compliance report"""
    
    # Access to sensitive resources
    secret_access = db.query(AuditLog).filter(
        and_(
            AuditLog.resource_type == 'secret',
            AuditLog.action == 'read',
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    ).count()
    
    # Failed authentication attempts
    failed_auth = db.query(AuditLog).filter(
        and_(
            AuditLog.event_type == 'user.login',
            AuditLog.status == 'failure',
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    ).count()
    
    # Privilege escalations
    role_changes = db.query(AuditLog).filter(
        and_(
            AuditLog.event_type == 'user.role_changed',
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    ).all()
    
    # High-risk operations
    high_risk = db.query(AuditLog).filter(
        and_(
            AuditLog.risk_level == 'high',
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    ).all()
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "summary": {
            "secret_access_count": secret_access,
            "failed_authentication_attempts": failed_auth,
            "role_changes": len(role_changes),
            "high_risk_operations": len(high_risk)
        },
        "details": {
            "role_changes": [
                {
                    "user": log.username,
                    "timestamp": log.timestamp,
                    "old_role": log.old_values.get('role') if log.old_values else None,
                    "new_role": log.new_values.get('role') if log.new_values else None,
                    "changed_by": log.metadata.get('changed_by') if log.metadata else None
                }
                for log in role_changes
            ],
            "high_risk_operations": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp,
                    "user": log.username,
                    "action": log.action,
                    "resource": f"{log.resource_type}/{log.resource_id}"
                }
                for log in high_risk
            ]
        }
    }