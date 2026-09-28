from sqlalchemy.orm import Session
from ...db.models import Case, Evidence
from ..platform.policy_engine import PolicyEngine
from ..platform.audit_ledger import AuditLedger
import uuid

class CaseManagementService:
    def __init__(self, db: Session, policy: PolicyEngine, audit: AuditLedger):
        self.db = db
        self.policy = policy
        self.audit = audit
        
    def create_case(self, user_id: int, username: str, case_number: str) -> Case:
        if not self.policy.check_authorization(user_id, "analyze_evidence"):
            raise PermissionError("Unauthorized to create cases.")
            
        case = Case(case_number=case_number)
        self.db.add(case)
        self.db.commit()
        
        self.audit.append_event(
            actor_username=username,
            action="CASE_CREATED",
            resource_id=case_number,
            details={"case_number": case_number}
        )
        return case
        
    def register_evidence(self, user_id: int, username: str, case_id: int, tag: str) -> Evidence:
        if not self.policy.check_authorization(user_id, "analyze_evidence"):
            raise PermissionError("Unauthorized to register evidence.")
            
        evidence = Evidence(case_id=case_id, evidence_tag=tag)
        self.db.add(evidence)
        self.db.commit()
        
        self.audit.append_event(
            actor_username=username,
            action="EVIDENCE_REGISTERED",
            resource_id=tag,
            details={"case_id": case_id, "tag": tag}
        )
        return evidence
