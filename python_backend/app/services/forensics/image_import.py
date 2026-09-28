import hashlib
import os
import logging
from typing import Optional, Literal, Dict, Any

logger = logging.getLogger(__name__)

class ImageImporter:
    def __init__(self, mode: Literal["standalone", "production"], db=None, policy=None, audit=None):
        self.mode = mode
        self.db = db
        self.policy = policy
        self.audit = audit
        
        if self.mode == "standalone":
            banner = "\n" + "="*80 + "\n"
            banner += "*** STANDALONE MODE — NO AUDIT LEDGER, NO CHAIN-OF-CUSTODY ENFORCEMENT — RESULTS NOT ADMISSIBLE ***\n"
            banner += "="*80 + "\n"
            print(banner)
            logger.warning(banner.strip())

    @classmethod
    def for_script(cls) -> "ImageImporter":
        return cls(mode="standalone")

    @classmethod
    def for_api(cls, db, policy, audit) -> "ImageImporter":
        if not db or not policy or not audit:
            raise ValueError("Production mode requires db, policy, and audit dependencies.")
        return cls(mode="production", db=db, policy=policy, audit=audit)

    def _compute_hash(self, filepath: str) -> str:
        sha256 = hashlib.sha256()
        try:
            # STRICT READ-ONLY OPEN
            with open(filepath, 'rb') as f:
                while chunk := f.read(1024 * 1024 * 4):  # 4MB chunks
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError as e:
            raise Exception(f"Failed to read image for hashing: {e}")

    def import_image(self, filepath: str, user_id: Optional[int] = None, username: Optional[str] = None, evidence_id: Optional[int] = None) -> Dict[str, Any]:
        size = os.path.getsize(filepath)
        current_hash = self._compute_hash(filepath)
        
        if self.mode == "standalone":
            return {"size": size, "hash": current_hash}
            
        # Production Mode Checks
        if not self.policy.check_authorization(user_id, "analyze_evidence"):
            raise PermissionError("Unauthorized to import evidence.")
            
        from app.db.models import Evidence
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise ValueError("Evidence not found.")
            
        if not evidence.original_hash:
            # First import - establish baseline
            evidence.original_hash = current_hash
            self.db.commit()
            self.audit.append_event(
                actor_username=username,
                action="IMAGE_HASH_BASELINE_ESTABLISHED",
                resource_id=evidence.evidence_tag,
                details={"hash": current_hash},
                sensitive_details={"path": filepath}
            )
        else:
            # Re-import - hard block on mismatch
            if current_hash != evidence.original_hash:
                self.audit.append_event(
                    actor_username=username,
                    action="IMAGE_HASH_MISMATCH",
                    resource_id=evidence.evidence_tag,
                    details={"expected": evidence.original_hash, "computed": current_hash},
                    sensitive_details={"path": filepath}
                )
                raise Exception(f"HARD BLOCK: Chain-of-custody Hash mismatch! Expected {evidence.original_hash}, got {current_hash}")
                
            self.audit.append_event(
                actor_username=username,
                action="IMAGE_HASH_VERIFIED",
                resource_id=evidence.evidence_tag,
                details={"hash": current_hash},
                sensitive_details={"path": filepath}
            )
            
        return {"size": size, "hash": current_hash}
