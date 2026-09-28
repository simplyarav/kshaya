import requests
from app.db.encrypted_db import SessionLocal
from app.db.models import User
from app.services.platform.auth import create_access_token

db = SessionLocal()
user = db.query(User).first()
token = create_access_token(data={"sub": str(user.id)})

res = requests.post('http://127.0.0.1:8000/api/drive-erasure/jobs/dry-run', 
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"device_id": "vdisk1"})
print(res.status_code)
print(res.text)
