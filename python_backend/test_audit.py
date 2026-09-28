import requests
from app.db.encrypted_db import SessionLocal
from app.db.models import User
from app.services.platform.auth import create_access_token

db = SessionLocal()
user = db.query(User).first()
token = create_access_token(data={"sub": user.id})

res = requests.get('http://127.0.0.1:8000/api/core/audit', headers={"Authorization": f"Bearer {token}"})
print(res.status_code)
print(res.text)
