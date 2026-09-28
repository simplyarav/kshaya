from sqlalchemy.orm import Session
from .gate import OnlineModeGate
from ...db.models import AuditEvent, Job
import urllib.request
import json

class CentralSyncService:
    def __init__(self, db: Session, target_url: str):
        self.db = db
        self.target_url = target_url
        
    def sync_metadata(self):
        """Syncs audit events and job summaries. Never syncs raw evidence."""
        OnlineModeGate.check(self.db)
        
        # Collect metadata
        events = self.db.query(AuditEvent).limit(100).all()
        jobs = self.db.query(Job).limit(100).all()
        
        payload = {
            "events": [{"id": e.id, "action": e.action} for e in events],
            "jobs": [{"id": j.id, "type": j.job_type, "status": j.status} for j in jobs]
        }
        
        # Emulate actual network sync
        req = urllib.request.Request(
            f"{self.target_url}/sync/metadata",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
