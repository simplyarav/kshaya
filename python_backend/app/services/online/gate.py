import json
from sqlalchemy.orm import Session
from ...db.models import SystemSetting

class OfflineModeException(Exception):
    """Raised when an online action is attempted while the system is in offline mode."""
    pass

class OnlineModeGate:
    @staticmethod
    def check(db: Session):
        """
        Enforces the offline-first NETWORK_POLICY.
        Raises OfflineModeException if online_mode is not explicitly enabled.
        """
        setting = db.query(SystemSetting).filter_by(key="online_mode").first()
        if not setting:
            raise OfflineModeException("Online Mode is disabled by default. Network operations are forbidden.")
            
        try:
            is_online = json.loads(setting.value_json)
        except json.JSONDecodeError:
            is_online = False
            
        if not is_online:
            raise OfflineModeException("Online Mode is disabled. Network operations are forbidden.")
