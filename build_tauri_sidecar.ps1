cd python_backend
python -m pip install pyinstaller
pyinstaller --name kshaya-backend --onefile --hidden-import uvicorn --hidden-import fastapi --hidden-import pydantic --hidden-import sqlalchemy app\main.py
mkdir -p ..\ui\src-tauri\bin
cp dist\kshaya-backend.exe ..\ui\src-tauri\bin\kshaya-backend-x86_64-pc-windows-msvc.exe
echo "Backend packaged for Tauri!"
