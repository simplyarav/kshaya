from sqlalchemy.orm import Session
from ..platform.policy_engine import PolicyEngine
from ..platform.certificate_generator import CertificateService
from ..platform.audit_ledger import AuditLedger
from ...db.models import Certificate, Job
import base64

class ForensicReportingService:
    def __init__(self, db: Session, cert_service: CertificateService, policy: PolicyEngine, audit: AuditLedger):
        self.db = db
        self.cert = cert_service
        self.policy = policy
        self.audit = audit
        
    def generate_report(self, user_id: int, username: str, report_data: dict, is_redacted: bool) -> bytes:
        if not self.policy.check_authorization(user_id, "approve_reports"):
            raise PermissionError("Approver role required to generate forensic reports.")
            
        template_key = "forensic_report_redacted" if is_redacted else "forensic_report"
        
        manifest = self.cert.generate_manifest(
            job_details=report_data,
            operator_identity=username,
            template_key=template_key
        )
        
        pdf_bytes = self.cert.generate_pdf(manifest)
        
        # Save to DB
        job = Job(job_type="forensic_report", status="completed")
        self.db.add(job)
        self.db.commit()
        
        cert = Certificate(job_id=job.id, manifest_json=manifest, pdf_bytes=base64.b64encode(pdf_bytes).decode('utf-8'))
        self.db.add(cert)
        self.db.commit()
        
        # Log to audit ledger
        self.audit.append_event(
            actor_username=username,
            action="FORENSIC_REPORT_GENERATED",
            resource_id=f"cert-{cert.id}",
            details={"redacted": is_redacted, "template": template_key}
        )
        
        return pdf_bytes
