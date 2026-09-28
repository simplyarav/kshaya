Set-Location python_backend
.\venv\Scripts\pyinstaller.exe --name kshaya-backend-x86_64-pc-windows-msvc --onefile --windowed 
    --hidden-import "uvicorn" --hidden-import "fastapi" --hidden-import "app.api" 
    --hidden-import "app.services" --hidden-import "pytsk3" --hidden-import "reportlab" 
    run.py
