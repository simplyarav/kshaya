from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
import platform
import ctypes
import os
import json

from ..db.encrypted_db import get_db
from ..db.models import Job, Certificate, AuditEvent, User, Role
from ..services.platform.policy_engine import PolicyEngine
from ..services.platform.audit_ledger import AuditLedger
from ..services.platform.auth import get_current_user, create_access_token
from ..services.platform.websocket_manager import ws_manager

router = APIRouter(tags=["Core"])

def get_policy(db: Session = Depends(get_db)):
    return PolicyEngine(db, AuditLedger(db))

def get_audit(db: Session = Depends(get_db)):
    return AuditLedger(db)

# ----------------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str # In real scenario, securely hashed

@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # Mocking password check. For real app, use bcrypt on user.hashed_password
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username")
        
    # Real app would verify req.password == user.hashed_password here
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "role": user.role.name}

# ----------------------------------------------------------------------------
# Setup & OS Elevation
# ----------------------------------------------------------------------------
@router.get("/setup/privilege-check")
def privilege_check():
    is_elevated = False
    try:
        if platform.system() == "Windows":
            is_elevated = ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            is_elevated = os.geteuid() == 0
    except Exception:
        pass
    
    # We allow the app to run without elevation, but destructive modules will be disabled
    return {"is_elevated": is_elevated, "behavior": "reduced_mode_if_false"}

@router.get("/setup/status")
def setup_status(db: Session = Depends(get_db)):
    # If no users exist, setup is required
    user_count = db.query(User).count()
    return {"is_initialized": user_count > 0}

class SetupRequest(BaseModel):
    admin_username: str
    admin_password: str
    lawful_authority_acknowledged: bool

@router.post("/setup/initialize")
def initialize_setup(req: SetupRequest, db: Session = Depends(get_db), audit: AuditLedger = Depends(get_audit)):
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Already initialized")
        
    if not req.lawful_authority_acknowledged:
        raise HTTPException(status_code=400, detail="Must acknowledge lawful authority")
        
    # Create master roles
    admin_role = Role(name="Admin", permissions=["access_dashboard", "view_audit", "analyze_evidence", "approve_reports", "execute_erasure", "view_certificates", "approve_exceptions"])
    db.add(admin_role)
    db.commit()
    
    # Create first user
    admin_user = User(username=req.admin_username, role_id=admin_role.id)
    db.add(admin_user)
    db.commit()
    
    # Audit log
    audit.append_event(
        actor_username=admin_user.username,
        action="FIRST_ADMIN_CREATED",
        resource_id=str(admin_user.id),
        details={"lawful_authority_acknowledged": True}
    )
    
    return {"status": "initialized"}

# ----------------------------------------------------------------------------
# Dashboard & Search
# ----------------------------------------------------------------------------
@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), policy: PolicyEngine = Depends(get_policy)):
    if not policy.check_authorization(current_user.id, "access_dashboard"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    jobs = db.query(Job).order_by(Job.started_at.desc()).limit(10).all()
    # Simple formatting for dashboard
    return {
        "recent_jobs": [{"id": j.id, "type": j.job_type, "status": j.status} for j in jobs],
        "alerts": [] # Mocked for now
    }

@router.get("/audit")
def get_audit_log(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), policy: PolicyEngine = Depends(get_policy)):
    if not policy.check_authorization(current_user.id, "view_audit"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    events = db.query(AuditEvent).order_by(AuditEvent.id.desc()).all()
    return [{"id": e.id, "action": e.action, "actor": e.actor_username, "timestamp": e.timestamp.isoformat()} for e in events]

@router.post("/audit/verify")
def verify_audit_chain(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), policy: PolicyEngine = Depends(get_policy), audit: AuditLedger = Depends(get_audit)):
    if not policy.check_authorization(current_user.id, "view_audit"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    is_valid, broken_id = audit.verify_chain(from_index=0)
    return {"valid": is_valid, "broken_id": broken_id}

@router.get("/search")
def global_search(q: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user), policy: PolicyEngine = Depends(get_policy)):
    if not policy.check_authorization(current_user.id, "access_dashboard"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    # Safe SQLAlchemy ORM search
    events = db.query(AuditEvent).filter(
        or_(
            AuditEvent.action.ilike(f"%{q}%"),
            AuditEvent.actor_username.ilike(f"%{q}%"),
            AuditEvent.resource_id.ilike(f"%{q}%")
        )
    ).limit(50).all()
    
    return {
        "audit_results": [{"id": e.id, "action": e.action, "actor": e.actor_username} for e in events]
    }

@router.get("/system/status")
def system_status(db: Session = Depends(get_db)):
    # Any active sanitisation job implies we are actively interacting with physical/mock hardware.
    active_jobs = db.query(Job).filter(Job.status == "in_progress").count()
    return {"simulation_mode_active": active_jobs > 0}

@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
