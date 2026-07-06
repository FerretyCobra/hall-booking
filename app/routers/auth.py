"""IT auth: session-cookie login for the dashboard."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import LoginIn
from ..security import verify_password, require_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Wrong username or password.")
    request.session["user"] = user.username
    return {"username": user.username, "role": user.role}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "signed out"}


@router.get("/me")
def me(user: User = Depends(require_admin)):
    return {"username": user.username, "role": user.role}
