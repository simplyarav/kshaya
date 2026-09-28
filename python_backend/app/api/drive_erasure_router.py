from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
import base64

from ..db.encrypted_db import get_db
from ..db.models import Certificate, User
from ..services.device.interface import DeviceLayer, SafetyViolation
from ..services.platform.policy_engine import PolicyEngine
from ..services.platform.audit_ledger import AuditLedger
from ..services.platform.certificate_generator import CertificateService
from ..services.platform.auth import get_current_user
from ..services.drive_erasure.method_selector import MethodSelector
from ..services.drive_erasure.job_orchestrator import JobOrchestrator

router = APIRouter(tags=["Drive Erasure"])

# Dependency injection placeholders
def get_device_layer():
    from ..services.device.windows_backend import WindowsDeviceBackend
    return DeviceLayer(backend=WindowsDeviceBackend())

def get_policy_engine(db: Session = Depends(get_db)):
    # Mocking audit ledger creation for dependency injection
    audit = AuditLedger(db)
    return PolicyEngine(db, audit)

def get_audit_ledger(db: Session = Depends(get_db)):
    return AuditLedger(db)

def get_cert_service():
    return CertificateService("key-123")

def get_job_orchestrator(
    db: Session = Depends(get_db),
    dev_layer: DeviceLayer = Depends(get_device_layer),
    policy: PolicyEngine = Depends(get_policy_engine),
    audit: AuditLedger = Depends(get_audit_ledger),
    cert: CertificateService = Depends(get_cert_service)
):
    return JobOrchestrator(db, dev_layer, policy, audit, cert)

# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
class ExecuteRequest(BaseModel):
    device_id: str
    method: str
    confirmed_serial: str

class DryRunRequest(BaseModel):
    device_id: str

# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------
@router.get("/devices")
def list_devices(dev_layer: DeviceLayer = Depends(get_device_layer), current_user: User = Depends(get_current_user)):
    return {"devices": dev_layer.list_devices()}

@router.get("/devices/{device_id}/capability")
def get_capability(device_id: str, dev_layer: DeviceLayer = Depends(get_device_layer), current_user: User = Depends(get_current_user)):
    cap = dev_layer.detect_capability(device_id)
    methods = MethodSelector.recommend_methods(cap)
    return {"capabilities": cap, "recommended_methods": methods}

@router.post("/jobs/dry-run")
def dry_run(req: DryRunRequest, orch: JobOrchestrator = Depends(get_job_orchestrator), current_user: User = Depends(get_current_user)):
    try:
        return orch.execute_dry_run(current_user.username, current_user.id, req.device_id)
    except SafetyViolation as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/jobs/execute")
async def execute_job(req: ExecuteRequest, orch: JobOrchestrator = Depends(get_job_orchestrator), current_user: User = Depends(get_current_user)):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        job = orch.execute_job(current_user.username, current_user.id, req.device_id, req.method, req.confirmed_serial, loop=loop)
        return {"status": "success", "job_id": job.id}
    except SafetyViolation as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from ..db.models import Job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    res = {"id": job.id, "status": job.status}
    if job.status == "completed":
        cert = db.query(Certificate).filter(Certificate.job_id == job.id).first()
        if cert:
            res["certificate_id"] = cert.id
    return res

@router.get("/certificates/{cert_id}")
def get_certificate(cert_id: int, db: Session = Depends(get_db), policy: PolicyEngine = Depends(get_policy_engine), current_user: User = Depends(get_current_user)):
    # Enforce RBAC
    if not policy.check_authorization(current_user.id, "view_certificates"):
        raise HTTPException(status_code=403, detail="Unauthorized to view certificates.")
        
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Not found")
    return cert.manifest_json

@router.get("/certificates/{cert_id}/download")
def download_certificate(cert_id: int, db: Session = Depends(get_db), policy: PolicyEngine = Depends(get_policy_engine), current_user: User = Depends(get_current_user)):
    # Enforce RBAC
    if not policy.check_authorization(current_user.id, "view_certificates"):
        raise HTTPException(status_code=403, detail="Unauthorized to download certificates.")
        
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert or not cert.pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF not found")
        
    pdf_bytes = base64.b64decode(cert.pdf_bytes)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=KSHAYA_Cert_{cert.id}.pdf"
    })
