"""Password hashing and the admin-session guard for IT routes."""
from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

# pbkdf2_sha256 is pure-Python (no native bcrypt build headaches on a LAN box).
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(raw: str) -> str:
    return pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd.verify(raw, hashed)


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency for IT-only endpoints. Reads the signed session cookie."""
    username = request.session.get("user")
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        request.session.clear()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session no longer valid.")
    return user
