import json
import csv
import io
from typing import List, Optional
from sqlalchemy.orm import Session

from ...db.models import AuditEvent
from .crypto import crypto_service

class AuditLedger:
    def __init__(self, db_session: Session):
        self.db = db_session

    def append_event(self, actor_username: str, action: str, resource_id: str, details: dict, sensitive_details: dict = None) -> AuditEvent:
        # Get the latest event for hash chaining
        last_event = self.db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
        prev_hash = last_event.event_hash if last_event else None

        # Build payload for hashing. EXCLUDE sensitive_details.
        # This guarantees offline verification of the redacted logs exported from the system.
        payload = {
            "actor": actor_username,
            "action": action,
            "resource_id": resource_id,
            "details": details,
            "prev_hash": prev_hash
        }
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        
        event_hash = crypto_service.sha512(payload_bytes).hex()
        signature = crypto_service.sign(payload_bytes).hex()

        new_event = AuditEvent(
            actor_username=actor_username,
            action=action,
            resource_id=resource_id,
            details=details,
            sensitive_details=sensitive_details,
            previous_hash=prev_hash,
            event_hash=event_hash,
            signature=signature
        )
        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)
        return new_event

    def verify_chain(self, from_index: int = 0) -> Optional[int]:
        """
        Walks the chain and confirms every hash link and signature.
        Returns the ID of the first broken link/event if tampering is detected,
        or None if the chain is fully valid.
        """
        events = self.db.query(AuditEvent).order_by(AuditEvent.id.asc()).offset(from_index).all()
        
        expected_prev_hash = None if from_index == 0 else (events[0].previous_hash if events else None)
        
        # We need the public key bytes for signature verification.
        # Inside the system we use our own private key's public part.
        from cryptography.hazmat.primitives import serialization
        pub_key_bytes = crypto_service._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        for event in events:
            # 1. Check hash link
            if expected_prev_hash is not None and event.previous_hash != expected_prev_hash:
                return event.id

            # 2. Recompute hash & Verify signature
            payload = {
                "actor": event.actor_username,
                "action": event.action,
                "resource_id": event.resource_id,
                "details": event.details,
                "prev_hash": event.previous_hash
            }
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            
            recomputed_hash = crypto_service.sha512(payload_bytes).hex()
            if recomputed_hash != event.event_hash:
                return event.id
                
            sig_bytes = bytes.fromhex(event.signature)
            is_valid = crypto_service.verify(payload_bytes, sig_bytes, pub_key_bytes)
            if not is_valid:
                return event.id

            expected_prev_hash = event.event_hash

        return None

    def batch_and_merkle_root(self, events: List[AuditEvent]) -> dict:
        """Compute a Merkle root for a given batch of events and sign it."""
        if not events:
            return None
            
        hashes = [bytes.fromhex(e.event_hash) for e in events]
        
        # Simple balanced merkle root derivation
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                h1 = hashes[i]
                h2 = hashes[i+1] if i+1 < len(hashes) else h1
                next_level.append(crypto_service.sha512(h1 + h2))
            hashes = next_level
            
        root_hex = hashes[0].hex()
        root_sig = crypto_service.sign(hashes[0]).hex()
        
        return {
            "root_hash": root_hex,
            "signature": root_sig,
            "event_count": len(events)
        }

    def export(self, format_type: str = "json") -> str:
        events = self.db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
        
        if format_type == "json":
            out = []
            for e in events:
                out.append({
                    "id": e.id,
                    "actor": e.actor_username,
                    "action": e.action,
                    "resource": e.resource_id,
                    "hash": e.event_hash,
                    "prev": e.previous_hash,
                    "timestamp": e.timestamp.isoformat()
                })
            return json.dumps(out, indent=2)
            
        elif format_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "actor", "action", "resource", "hash", "timestamp"])
            for e in events:
                writer.writerow([e.id, e.actor_username, e.action, e.resource_id, e.event_hash, e.timestamp.isoformat()])
            return output.getvalue()
            
        return ""
