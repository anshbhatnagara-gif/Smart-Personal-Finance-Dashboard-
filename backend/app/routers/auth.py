"""Authentication Router: User registration, login, and current profile."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ResponseBase
from app.schemas.user import UserCreate, UserLogin, UserUpdate, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ResponseBase[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User"
)
async def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> ResponseBase[TokenResponse]:
    """Register a new user account and return a JWT access token."""
    user = AuthService.register_user(db, user_in)
    token_resp = AuthService.generate_token_response(user)
    return ResponseBase(
        success=True,
        message="User account created successfully",
        data=token_resp
    )


@router.post(
    "/login",
    response_model=ResponseBase[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User Login"
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
) -> ResponseBase[TokenResponse]:
    """Authenticate user with email and password to receive a JWT access token."""
    user = AuthService.authenticate_user(db, credentials)
    token_resp = AuthService.generate_token_response(user)
    return ResponseBase(
        success=True,
        message="Authentication successful",
        data=token_resp
    )


@router.get(
    "/me",
    response_model=ResponseBase[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Current User Profile"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> ResponseBase[UserResponse]:
    """Get profile information of the currently authenticated user."""
    return ResponseBase(
        success=True,
        message="User profile retrieved",
        data=UserResponse.model_validate(current_user)
    )


@router.put(
    "/me",
    response_model=ResponseBase[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Current User Profile"
)
@router.patch(
    "/me",
    response_model=ResponseBase[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Current User Profile (Patch)"
)
async def update_current_user_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ResponseBase[UserResponse]:
    """Update profile information of the currently authenticated user."""
    updated_user = AuthService.update_user(db, current_user, user_in)
    return ResponseBase(
        success=True,
        message="User profile updated successfully",
        data=UserResponse.model_validate(updated_user)
    )
