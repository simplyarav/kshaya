import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KSHAYA Local Backend")

# Ensure the backend only binds to localhost
if settings.HOST != "127.0.0.1":
    logger.error(f"SECURITY VIOLATION: Refusing to start on non-localhost interface {settings.HOST}")
    sys.exit(1)
logger.info(f"Starting KSHAYA backend strictly on {settings.HOST}:{settings.PORT}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be tightened in production to Tauri's local origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    import time
    start = time.time()
    try:
        response = await call_next(request)
        with open("C:\\Program Files\\kshaya\\requests.log", "a") as f:
            f.write(f"{request.method} {request.url.path} {response.status_code}\n")
        return response
    except Exception as e:
        with open("C:\\Program Files\\kshaya\\requests.log", "a") as f:
            f.write(f"{request.method} {request.url.path} ERROR: {str(e)}\n")
        raise

from .api.drive_erasure_router import router as drive_erasure_router
from .api.file_erasure_router import router as file_erasure_router
from .api.forensics_router import router as forensics_router
from .api.core_router import router as core_router
from .db.encrypted_db import init_db

# Initialize database tables
init_db()

app.include_router(core_router, prefix="/api/core")
app.include_router(drive_erasure_router, prefix="/api/drive-erasure")
app.include_router(file_erasure_router, prefix="/api/file-erasure")
app.include_router(forensics_router, prefix="/api/forensics")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "KSHAYA Local Backend"}
