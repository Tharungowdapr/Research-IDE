"""
Authentication Routes: Register, Login, Refresh, Me
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from models.user import User

router = APIRouter()

# Simple in-memory rate limiter (production: use slowapi or Redis-backed limiter)
_login_attempts: dict = {}
_MAX_LOGIN_ATTEMPTS = 10
_LOCKOUT_SECONDS = 300


def _check_rate_limit(key: str, max_attempts: int, window: int) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    import time
    now = time.time()
    if key in _login_attempts:
        attempts, first_at = _login_attempts[key]
        if now - first_at > window:
            _login_attempts.pop(key, None)
            return True
        if attempts >= max_attempts:
            return False
        _login_attempts[key] = (attempts + 1, first_at)
    else:
        _login_attempts[key] = (1, now)
    return True


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    skill_level: str = "intermediate"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    skill_level: str | None = None
    interests: list | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    # Rate limit: 3 registrations per minute per IP
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(f"register:{client_ip}", 3, 60):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Try again later.")
    try:
        # Check email uniqueness
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Validate password strength
        if len(body.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        user = User(
            email=body.email,
            password_hash=hash_password(body.password),
            name=body.name,
            skill_level=body.skill_level,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": _user_response(user),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login")
async def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Rate limit: 5 login attempts per minute per IP
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(f"login:{client_ip}", 5, 60):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in a minute.")

    # Account-level lockout check
    if not _check_rate_limit(f"login_account:{body.email}", _MAX_LOGIN_ATTEMPTS, _LOCKOUT_SECONDS):
        raise HTTPException(status_code=429, detail="Account temporarily locked due to too many failed attempts.")

    user = db.query(User).filter(User.email == body.email).first()

    if not user or not verify_password(body.password, user.password_hash):
        # Still count toward account lockout on failure
        _check_rate_limit(f"login_account:{body.email}", _MAX_LOGIN_ATTEMPTS, _LOCKOUT_SECONDS)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_response(user),
    }


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token({"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name is not None:
        current_user.name = body.name
    if body.skill_level is not None:
        current_user.skill_level = body.skill_level
    if body.interests is not None:
        current_user.interests = body.interests
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_response(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "skill_level": user.skill_level,
        "interests": user.interests or [],
        "preferred_provider": user.preferred_provider,
        "preferred_model": user.preferred_model,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
