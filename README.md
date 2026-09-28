# KSHAYA

**Offline-first, authorised-use-only digital forensics and media sanitisation platform.**

## Project Structure
- `ui/` - Tauri + React + TypeScript + Tailwind CSS desktop shell
- `python_backend/` - Local Python FastAPI backend

## Prerequisites
- Node.js (v18+)
- Rust & Cargo (for Tauri build)
- Python 3.11+
- [SQLCipher](https://www.zetetic.net/sqlcipher/) / `pysqlcipher3` prerequisites

## Setup & Run Instructions

### 1. Python Backend
The backend is a local FastAPI server strictly bound to `127.0.0.1`.

**Windows:**
```powershell
cd python_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn
# You also need to install pysqlcipher3 or use a precompiled sqlite3 with sqlcipher support
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Linux:**
```bash
cd python_backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn
# Install sqlcipher: sudo apt-get install sqlcipher libsqlite3-dev
# Install pysqlcipher3
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

#### Packaging the Backend as a Tauri Sidecar
The backend will eventually be packaged using PyInstaller.
```bash
# Inside python_backend/
pip install pyinstaller
pyinstaller --onefile app/main.py --name kshaya-backend
```
Then copy the executable to `ui/src-tauri/bin/kshaya-backend-<target-triple>` (e.g. `kshaya-backend-x86_64-pc-windows-msvc.exe`) for Tauri to bundle it automatically.

### 2. Tauri UI
The UI is a standard React + Vite app running inside the Tauri shell.

**Windows & Linux:**
```bash
cd ui
npm install
# Run in dev mode (requires Rust and the Python backend to be running)
npm run tauri dev
```

## Network Policy
Please see [NETWORK_POLICY.md](./NETWORK_POLICY.md) for strict rules regarding offline-first behavior and outbound network requests.
