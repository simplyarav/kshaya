import subprocess
import time
import requests
import sys

# Start uvicorn
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"])
time.sleep(3)

try:
    res = requests.post('http://127.0.0.1:8000/api/core/setup/initialize', json={
        'admin_username': 'testuser',
        'admin_password': 'password',
        'lawful_authority_acknowledged': True
    })
    print(res.status_code)
    print(res.text)
finally:
    proc.terminate()
