import sys
import traceback
from fastapi.testclient import TestClient
from app.main import app

try:
    client = TestClient(app)
    res = client.post("/api/core/setup/initialize", json={
        "admin_username": "testuser",
        "admin_password": "password",
        "lawful_authority_acknowledged": True
    })
    print(res.status_code)
    print(res.text)
except Exception as e:
    traceback.print_exc(file=sys.stdout)
