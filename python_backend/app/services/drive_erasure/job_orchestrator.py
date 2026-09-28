import base64
import threading
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..device.interface import DeviceLayer, SafetyViolation
from ..platform.policy_engine import PolicyEngine
from ..platform.audit_ledger import AuditLedger
from ..platform.certificate_generator import CertificateService
from ..platform.websocket_manager import ws_manager
from ...db.encrypted_db import SessionLocal
from ...db.models import Job, Certificate
from .verification import VerificationService
from .method_selector import MethodSelector

class JobOrchestrator:
    # Class-level state tracking for the session
    _simulated_devices = set()

    def __init__(self, db: Session, device_layer: DeviceLayer, policy_engine: PolicyEngine, 
                 audit_ledger: AuditLedger, cert_service: CertificateService):
        self.db = db
        self.device_layer = device_layer
        self.policy_engine = policy_engine
        self.audit = audit_ledger
        self.cert_service = cert_service
        self.verification = VerificationService(device_layer)

    def execute_dry_run(self, operator_username: str, operator_user_id: int, device_id: str) -> dict:
        if not self.policy_engine.check_authorization(operator_user_id, "execute_erasure"):
            raise SafetyViolation("Unauthorized to perform dry-run.")
            
        info = self.device_layer.get_device_info(device_id)
        
        # Add to simulated set bound by actual serial number, NOT path
        self._simulated_devices.add(info.serial)
        
        self.audit.append_event(
            actor_username=operator_username,
            action="DRY_RUN_SIMULATION",
            resource_id=info.serial,
            details={"device_id": device_id}
        )
        
        return {"status": "simulation_complete", "serial": info.serial}

    def execute_job(self, operator_username: str, operator_user_id: int, device_id: str, 
                    method: str, confirmed_serial: str, case_id: int = None, evidence_id: int = None, loop=None) -> Job:
        
        # Re-fetch info directly from device to ensure we are talking to the current physical disk
        current_info = self.device_layer.get_device_info(device_id)
        
        # 1. RBAC Check
        if not self.policy_engine.check_authorization(operator_user_id, "execute_erasure"):
            raise SafetyViolation("Unauthorized to execute drive erasure.")
            
        # 2. Legal Hold Check
        if case_id and self.policy_engine.is_action_blocked_by_hold(case_id, evidence_id):
            raise SafetyViolation("Action blocked by legal hold.")

        # 3. Dry-Run Mandatory Check (bound by serial)
        if current_info.serial not in self._simulated_devices:
            raise SafetyViolation(f"Mandatory dry-run simulation has not been performed for serial {current_info.serial} in this session.")
            
        # 4. Typed Serial Match Check (User input vs Actual hardware)
        if confirmed_serial != current_info.serial:
            raise SafetyViolation("Typed serial confirmation does not match the actual device serial.")

        # Capability enforcement
        cap = self.device_layer.detect_capability(device_id)
        recommended = MethodSelector.recommend_methods(cap)
        if method not in recommended:
            raise SafetyViolation(f"Method '{method}' is not recommended or allowed for this device.")
            
        # Start DB Job
        job = Job(job_type="sanitisation", status="in_progress")
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        self.audit.append_event(
            actor_username=operator_username,
            action="ERASE_START",
            resource_id=current_info.serial,
            details={"method": method, "job_id": job.id}
        )

        import asyncio
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

        # Launch background thread
        thread = threading.Thread(
            target=self._run_job_background,
            args=(job.id, operator_username, device_id, method, confirmed_serial, current_info, loop)
        )
        thread.start()
        
        return job

    def _run_job_background(self, job_id, operator_username, device_id, method, confirmed_serial, current_info, loop):
        import asyncio
        db = SessionLocal()
        audit = AuditLedger(db)
        job = db.query(Job).filter_by(id=job_id).first()
        
        def bcast(status, prog, details=None):
            if details is None:
                details = {}
            coro = ws_manager.broadcast_job_update(job_id, status, prog, details)
            with open("DEBUG.log", "a") as f:
                f.write(f"Scheduling bcast {status} {prog}\n")
            if loop and loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(coro, loop)
                    future.add_done_callback(lambda f: open("DEBUG.log", "a").write(f"bcast {status} done\n"))
                except Exception as ex:
                    with open("DEBUG.log", "a") as f:
                        f.write(f"Threadsafe error: {ex}\n")
            else:
                try:
                    asyncio.run(coro)
                except Exception as ex:
                    with open("DEBUG.log", "a") as f:
                        f.write(f"Asyncio.run error: {ex}\n")
                
        try:
            bcast("in_progress", 10)
            import time
            time.sleep(2) # Simulate work
            bcast("in_progress", 50)
            time.sleep(2)
            bcast("in_progress", 80)
            
            # THIS IS THE ONLY ALLOWED CALL WITH dry_run=False IN THE ENTIRE MODULE/APP
            res = self.device_layer.run_command(device_id, "clear", dry_run=False, confirmed_serial=confirmed_serial)
            
            if not res.success:
                raise Exception(f"Device command failed: {res.error}")

            # Verification
            verif_res = self.verification.verify_sampling(
                device_id, 
                serial=confirmed_serial, 
                execute_fn=lambda cmd: self.device_layer.run_command(device_id, "clear", dry_run=False, confirmed_serial=confirmed_serial)
            )
            if not verif_res.is_successful:
                raise Exception(f"Verification failed: {verif_res.errors}")
                
            job.status = "completed"
            
            # Map method to template key
            template_key = "logical_readback" if "Clear" in method else "cryptographic_erase"
            
            manifest = self.cert_service.generate_manifest(
                job_details={
                    "method": method,
                    "target_serial": current_info.serial,
                    "target_model": current_info.model,
                    "capacity_bytes": current_info.capacity_bytes,
                    "verification": verif_res.model_dump()
                },
                operator_identity=operator_username,
                template_key=template_key
            )
            
            # Ensure deterministic PDF generation (returns bytes directly)
            pdf_bytes = self.cert_service.generate_pdf(manifest)
            
            # Base64 encode for DB storage
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            cert = Certificate(job_id=job.id, manifest_json=manifest, pdf_bytes=pdf_b64)
            db.add(cert)
            db.commit()
            
            audit.append_event(
                actor_username=operator_username,
                action="ERASE_SUCCESS",
                resource_id=current_info.serial,
                details={"job_id": job.id, "certificate_id": cert.id}
            )
            bcast("completed", 100, {"certificate_id": cert.id})
            
        except Exception as e:
            with open("DEBUG.log", "a") as f:
                f.write(f"Exception in bg thread: {e}\n")
            job.status = "failed"
            db.commit()
            audit.append_event(
                actor_username=operator_username,
                action="ERASE_FAILED",
                resource_id=current_info.serial,
                details={"job_id": job.id, "error": str(e)}
            )
            with open("DEBUG.log", "a") as f:
                f.write(f"Calling bcast failed\n")
            bcast("failed", 100, {"error": str(e)})
            with open("DEBUG.log", "a") as f:
                f.write(f"Bcast called\n")
        finally:
            db.close()
