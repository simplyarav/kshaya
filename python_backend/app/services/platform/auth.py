import jwt
import datetime
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from ...db.encrypted_db import get_db
from ...db.models import User

# In a real app this would be loaded from a secure environment variable
SECRET_KEY = "kshaya-offline-secret-key-change-me"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: datetime.timedelta = datetime.timedelta(hours=12)):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
        
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub_str = payload.get("sub")
        if sub_str is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user_id = int(sub_str)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user
