"""Auth routes."""

from fastapi import APIRouter, Query, Request, status
from pydantic import BaseModel, EmailStr

from app.api.deps import AuthServiceDep, CurrentUser, client_meta
from app.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class ResendByEmailRequest(BaseModel):
    email: EmailStr


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, auth: AuthServiceDep) -> dict:
    user, email_meta = await auth.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return {
        "user": user,
        "verification_required": True,
        **email_meta,
    }


@router.post("/login")
async def login(body: LoginRequest, request: Request, auth: AuthServiceDep) -> dict:
    user_agent, ip = client_meta(request)
    user, tokens = await auth.login(
        email=body.email,
        password=body.password,
        user_agent=user_agent,
        ip_address=ip,
    )
    return {"user": user, "tokens": tokens}


@router.post("/verify-email", response_model=UserResponse)
async def verify_email_post(body: VerifyEmailRequest, auth: AuthServiceDep) -> UserResponse:
    return await auth.verify_email(body.token)


@router.get("/verify-email", response_model=UserResponse)
async def verify_email_get(
    auth: AuthServiceDep,
    token: str = Query(..., min_length=10),
) -> UserResponse:
    return await auth.verify_email(token)


@router.post("/resend-verification")
async def resend_verification(user: CurrentUser, auth: AuthServiceDep) -> dict:
    meta = await auth.resend_verification(user.id)
    out: dict = {
        "message": str(meta.get("message") or "OK"),
        "email_sent": bool(meta.get("email_sent")),
    }
    if meta.get("verification_url"):
        out["verification_url"] = meta["verification_url"]
    return out


@router.post("/resend-verification-email")
async def resend_verification_email(
    body: ResendByEmailRequest, auth: AuthServiceDep
) -> dict:
    """Public resend — used when login is blocked until Gmail verify."""
    meta = await auth.resend_verification_by_email(str(body.email))
    out: dict = {
        "message": str(meta.get("message") or "OK"),
        "email_sent": bool(meta.get("email_sent")),
    }
    if meta.get("verification_url"):
        out["verification_url"] = meta["verification_url"]
    return out


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, request: Request, auth: AuthServiceDep) -> TokenPair:
    user_agent, ip = client_meta(request)
    return await auth.refresh(body.refresh_token, user_agent=user_agent, ip_address=ip)


@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshRequest, auth: AuthServiceDep) -> MessageResponse:
    await auth.logout(body.refresh_token)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser, auth: AuthServiceDep) -> UserResponse:
    return await auth.get_user(user.id)
