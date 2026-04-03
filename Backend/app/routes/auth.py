from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import get_db
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_token
)

router = APIRouter()


class SignupRequest(BaseModel):
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str


@router.post("/auth/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    
    # Validate passwords match
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Validate password length
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    try:
        user = create_user(db, request.email, request.password)
        token = create_access_token(user.id, user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login a user."""
    
    try:
        user = authenticate_user(db, request.email, request.password)
        token = create_access_token(user.id, user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/verify")
async def verify_token_endpoint(token: str):
    """Verify if a token is valid."""
    try:
        payload = verify_token(token)
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
