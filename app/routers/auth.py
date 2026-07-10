"""IT auth: session-cookie login for the dashboard."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db, transaction
from ..models import User
from ..schemas import LoginIn, CredentialsUpdateIn
from ..security import verify_password, require_admin, hash_password

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


@router.post("/credentials")
def update_credentials(payload: CredentialsUpdateIn, request: Request,
                       user: User = Depends(require_admin), db: Session = Depends(get_db)):
    new_user = payload.new_username.strip()
    if not new_user:
        raise HTTPException(400, "Username cannot be empty.")
    if not payload.new_password:
        raise HTTPException(400, "Password cannot be empty.")
        
    existing = db.query(User).filter(User.username == new_user, User.id != user.id).first()
    if existing:
        raise HTTPException(409, "Username already taken.")

    with transaction(db):
        user.username = new_user
        user.password_hash = hash_password(payload.new_password)
        request.session["user"] = new_user
        
    return {"status": "credentials updated", "username": new_user}
