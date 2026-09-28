from sqlalchemy.orm import Session
from ..platform.policy_engine import PolicyEngine
from ..platform.audit_ledger import AuditLedger

class EWasteTrackingService:
    def __init__(self, db: Session, policy_engine: PolicyEngine, audit_ledger: AuditLedger):
        self.db = db
        self.policy = policy_engine
        self.audit = audit_ledger

    def record_disposition(self, user_id: int, username: str, serial: str, disposition: str, cert_id: int):
        if not self.policy.check_authorization(user_id, "track_ewaste"):
            raise Exception("Unauthorized to track e-waste disposition.")
            
        if disposition not in ["wiped-for-reuse", "sent-for-destruction"]:
            raise ValueError("Invalid disposition type.")
            
        self.audit.append_event(
            actor_username=username,
            action="DISPOSITION_RECORDED",
            resource_id=serial,
            details={"disposition": disposition, "certificate_id": cert_id}
        )
        return True
