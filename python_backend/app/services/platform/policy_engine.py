from typing import Optional
from sqlalchemy.orm import Session
from ...db.models import User, Role, Case, Evidence, Policy
from .audit_ledger import AuditLedger

class PolicyEngine:
    def __init__(self, db_session: Session, audit_ledger: AuditLedger):
        self.db = db_session
        self.audit = audit_ledger

    def check_authorization(self, user_id: int, action: str, resource: str = None) -> bool:
        """Generic RBAC checker for Operator, Approver, Auditor, Admin."""
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user or not user.role:
            return False
            
        permissions = user.role.permissions
        if "*" in permissions or action in permissions:
            return True
        return False

    def is_action_blocked_by_hold(self, case_id: int, evidence_id: int = None) -> bool:
        """Checks legal-hold and active-evidence flags per case/device/file."""
        case = self.db.query(Case).filter_by(id=case_id).first()
        if case and case.legal_hold:
            return True
            
        if evidence_id:
            evidence = self.db.query(Evidence).filter_by(id=evidence_id).first()
            if evidence and evidence.active_evidence:
                return True
                
        return False

    def update_policy(self, admin_username: str, version: str, new_config: dict):
        """Creates a new policy version and logs it to the AuditLedger."""
        policy = Policy(version=version, config=new_config)
        self.db.add(policy)
        self.db.commit()
        
        self.audit.append_event(
            actor_username=admin_username,
            action="POLICY_UPDATED",
            resource_id=version,
            details=new_config
        )
        return policy

    def request_exception(self, operator_username: str, action: str, reason: str) -> str:
        """
        Operator requests an exception to a policy block.
        Returns an exception request ID.
        """
        # In a full implementation, this would save an ExceptionRequest record to DB.
        # For scaffolding, we just log the request to the ledger.
        req_id = f"EXC-REQ-{operator_username}-{action}"
        self.audit.append_event(
            actor_username=operator_username,
            action="EXCEPTION_REQUESTED",
            resource_id=req_id,
            details={"action_requested": action, "reason": reason}
        )
        return req_id

    def approve_exception(self, approver_username: str, approver_user_id: int, req_id: str) -> bool:
        """
        Approver-role user signs off on an exception.
        The approval action itself must be auditable, writing its own signed event to AuditLedger.
        """
        if not self.check_authorization(approver_user_id, "approve_exceptions"):
            self.audit.append_event(
                actor_username=approver_username,
                action="EXCEPTION_APPROVAL_DENIED",
                resource_id=req_id,
                details={"reason": "Unauthorized approver"}
            )
            return False
            
        self.audit.append_event(
            actor_username=approver_username,
            action="EXCEPTION_APPROVED",
            resource_id=req_id,
            details={"approved": True}
        )
        return True
