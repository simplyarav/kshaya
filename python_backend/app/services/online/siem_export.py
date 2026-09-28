from sqlalchemy.orm import Session
from .gate import OnlineModeGate
import socket
import json

class SIEMExportService:
    def __init__(self, db: Session, syslog_host: str, syslog_port: int = 514):
        self.db = db
        self.host = syslog_host
        self.port = syslog_port
        
    def push_event(self, event_data: dict):
        """Pushes an audit event to a remote SIEM via Syslog UDP."""
        OnlineModeGate.check(self.db)
        
        message = json.dumps(event_data).encode('utf-8')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(message, (self.host, self.port))
        finally:
            sock.close()
