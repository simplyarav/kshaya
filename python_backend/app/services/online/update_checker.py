from sqlalchemy.orm import Session
from .gate import OnlineModeGate
import urllib.request
import json

class UpdateChecker:
    def __init__(self, db: Session, update_url: str):
        self.db = db
        self.update_url = update_url
        
    def check_for_updates(self):
        """Checks for signed update manifest. Never uploads anything."""
        OnlineModeGate.check(self.db)
        
        req = urllib.request.Request(f"{self.update_url}/manifest.json", method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return {"latest_version": data.get("version"), "signature": data.get("signature")}
