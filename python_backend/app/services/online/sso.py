from sqlalchemy.orm import Session
from .gate import OnlineModeGate
import urllib.request
import json

class SSOService:
    def __init__(self, db: Session, oidc_issuer_url: str):
        self.db = db
        self.issuer_url = oidc_issuer_url
        
    def authenticate_via_oidc(self, auth_code: str):
        """Alternative to local RBAC accounts."""
        OnlineModeGate.check(self.db)
        
        req = urllib.request.Request(
            f"{self.issuer_url}/token",
            data=json.dumps({"code": auth_code}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return {"username": data.get("preferred_username"), "sso_id": data.get("sub")}
