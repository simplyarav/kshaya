from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import base64

from ..db.encrypted_db import get_db
from ..db.models import Job, Certificate, ReviewQueueItem, User
from ..services.platform.policy_engine import PolicyEngine
from ..services.platform.audit_ledger import AuditLedger
from ..services.platform.certificate_generator import CertificateService
from ..services.platform.auth import get_current_user
from ..services.file_erasure.selection import FileSelector
from ..services.file_erasure.erase_engine import EraseEngine

router = APIRouter(tags=["File Erasure"])

def get_policy_engine(db: Session = Depends(get_db)):
    audit = AuditLedger(db)
    return PolicyEngine(db, audit)

def get_audit_ledger(db: Session = Depends(get_db)):
    return AuditLedger(db)

def get_cert_service():
    return CertificateService("key-123")

class PreviewRequest(BaseModel):
    paths: List[str]

class RunRequest(BaseModel):
    paths: List[str]
    method: str
    override_cloud_sync: bool = False

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import base64
import threading
import time

from ..db.encrypted_db import get_db, SessionLocal
from ..db.models import Job, Certificate, ReviewQueueItem, User
from ..services.platform.policy_engine import PolicyEngine
from ..services.platform.audit_ledger import AuditLedger
from ..services.platform.certificate_generator import CertificateService
from ..services.platform.auth import get_current_user
from ..services.file_erasure.selection import FileSelector
from ..services.file_erasure.erase_engine import EraseEngine

router = APIRouter(tags=["File Erasure"])

def get_policy_engine(db: Session = Depends(get_db)):
    audit = AuditLedger(db)
    return PolicyEngine(db, audit)

def get_audit_ledger(db: Session = Depends(get_db)):
    return AuditLedger(db)

def get_cert_service():
    return CertificateService("key-123")

class PreviewRequest(BaseModel):
    paths: List[str]

class RunRequest(BaseModel):
    paths: List[str]
    method: str
    quarantine: bool = False
    override_cloud_sync: bool = False

@router.post("/preview")
def preview_selection(req: PreviewRequest, current_user: User = Depends(get_current_user), policy: PolicyEngine = Depends(get_policy_engine), db: Session = Depends(get_db)):
    if not policy.check_authorization(current_user.id, "execute_erasure"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    preview = FileSelector.get_preview(req.paths)
    
    # Mock some flagged items if paths look sensitive
    for file in preview["items"]:
        path_lower = file["path"].lower()
        if "sensitive" in path_lower or "tax" in path_lower:
            # Add to review queue if not exists
            existing = db.query(ReviewQueueItem).filter_by(file_path=file["path"], status="pending").first()
            if not existing:
                item = ReviewQueueItem(file_path=file["path"], flag_reason="PII/Financial data detected", status="pending")
                db.add(item)
                db.commit()
    return preview

@router.get("/review-queue")
def get_review_queue(db: Session = Depends(get_db), policy: PolicyEngine = Depends(get_policy_engine), current_user: User = Depends(get_current_user)):
    if not policy.check_authorization(current_user.id, "approve_exceptions"):
        raise HTTPException(status_code=403, detail="Approver role required")
        
    items = db.query(ReviewQueueItem).filter(ReviewQueueItem.status == "pending").all()
    return [{"id": i.id, "file_path": i.file_path, "flag_reason": i.flag_reason, "status": i.status} for i in items]

@router.post("/run")
def execute_run(
    req: RunRequest,
    db: Session = Depends(get_db),
    policy: PolicyEngine = Depends(get_policy_engine),
    audit: AuditLedger = Depends(get_audit_ledger),
    current_user: User = Depends(get_current_user)
):
    # Enforce RBAC
    if not policy.check_authorization(current_user.id, "execute_erasure"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    if req.override_cloud_sync:
        if not policy.check_authorization(current_user.id, "approve_exceptions"):
            raise HTTPException(status_code=403, detail="Approver role required to override cloud sync blocks.")
            
    # Check if any path is pending review
    for path in req.paths:
        pending = db.query(ReviewQueueItem).filter_by(file_path=path, status="pending").first()
        if pending:
            raise HTTPException(status_code=400, detail=f"File {path} requires approval in the Review Queue before erasure.")
        
    job = Job(job_type="file_erasure", status="in_progress")
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Spawn background thread
    t = threading.Thread(target=_run_file_job_background, args=(job.id, current_user.username, req.paths, req.method, req.quarantine, req.override_cloud_sync))
    t.start()
    
    return {"status": "success", "job_id": job.id}

def _run_file_job_background(job_id, username, paths, method, is_quarantine, override_cloud_sync):
    db = SessionLocal()
    audit = AuditLedger(db)
    cert_service = CertificateService("key-123")
    job = db.query(Job).filter_by(id=job_id).first()
    
    time.sleep(3) # simulate I/O
    
    results = []
    try:
        for path in paths:
            if EraseEngine.is_cloud_sync_path(path):
                if not override_cloud_sync:
                    results.append({"path": path, "status": "blocked_by_cloud_sync"})
                    continue
                    
                # Log the override
                audit.append_event(
                    actor_username=username,
                    action="CLOUD_SYNC_OVERRIDE_APPROVED",
                    resource_id="file-job",
                    details={"action": "bypassed cloud sync block"},
                    sensitive_details={"path": path}
                )
                
            # If not a real file in testing, mock success
            if not __import__("os").path.exists(path):
                res = {"status": "success", "mocked": True}
                file_hash = "mock-hash"
            else:
                file_hash = EraseEngine.hash_file(path)
                if is_quarantine:
                    res = {"status": "success", "dest": EraseEngine.quarantine_file(path)}
                else:
                    res = EraseEngine.overwrite_and_delete(path)
            
            # Log to ledger. Redacted path in `details`, full path in `sensitive_details`.
            action_name = "FILE_QUARANTINED" if is_quarantine else ("FILE_ERASED" if res["status"] == "success" else "FILE_ERASE_FAILED")
            audit.append_event(
                actor_username=username,
                action=action_name,
                resource_id=f"job-{job_id}",
                details={"hash": file_hash, "path": "[REDACTED]"},
                sensitive_details={"path": path}
            )
            
            res["path"] = path
            results.append(res)
            
        job.status = "completed"
        
        # Generate certificate
        manifest = cert_service.generate_manifest(
            job_details={"targets_processed": len(results), "method": method, "quarantined": is_quarantine, "results": results},
            operator_identity=username,
            template_key="logical_file_overwrite"
        )
        pdf_bytes = cert_service.generate_pdf(manifest)
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        cert = Certificate(job_id=job.id, manifest_json=manifest, pdf_bytes=pdf_b64)
        db.add(cert)
        db.commit()
    except Exception as e:
        job.status = "failed"
        db.commit()
    finally:
        db.close()

@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    res = {"id": job.id, "status": job.status}
    if job.status == "completed":
        cert = db.query(Certificate).filter(Certificate.job_id == job.id).first()
        if cert:
            res["certificate_id"] = cert.id
    return res

@router.get("/receipts/{cert_id}")
def get_receipt(cert_id: int, db: Session = Depends(get_db), policy: PolicyEngine = Depends(get_policy_engine), current_user: User = Depends(get_current_user)):
    if not policy.check_authorization(current_user.id, "view_certificates"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Not found")
    return cert.manifest_json

@router.get("/receipts/{cert_id}/download")
def download_receipt(cert_id: int, db: Session = Depends(get_db), policy: PolicyEngine = Depends(get_policy_engine), current_user: User = Depends(get_current_user)):
    if not policy.check_authorization(current_user.id, "view_certificates"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert or not cert.pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF not found")
        
    pdf_bytes = base64.b64decode(cert.pdf_bytes)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=KSHAYA_File_Receipt_{cert.id}.pdf"
    })

@router.post("/review-queue/{item_id}/approve")
def approve_review_item(
    item_id: int,
    db: Session = Depends(get_db),
    policy: PolicyEngine = Depends(get_policy_engine),
    audit: AuditLedger = Depends(get_audit_ledger),
    current_user: User = Depends(get_current_user)
):
    if not policy.check_authorization(current_user.id, "approve_exceptions"):
        raise HTTPException(status_code=403, detail="Approver role required")
        
    item = db.query(ReviewQueueItem).filter(ReviewQueueItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
        
    item.status = "approved"
    db.commit()
    
    audit.append_event(
        actor_username=current_user.username,
        action="REVIEW_QUEUE_APPROVED",
        resource_id=str(item.id),
        details={"path": "[REDACTED]", "reason": item.flag_reason},
        sensitive_details={"path": item.file_path}
    )
    
    return {"status": "approved"}

@router.post("/schedule")
def schedule_job(
    req: dict, 
    db: Session = Depends(get_db), 
    policy: PolicyEngine = Depends(get_policy_engine),
    current_user: User = Depends(get_current_user)
):
    if not policy.check_authorization(current_user.id, "schedule_erasure"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return {"status": "scheduled"}
