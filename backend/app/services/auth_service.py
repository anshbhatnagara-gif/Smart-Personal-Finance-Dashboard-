"""Authentication Service: User registration, password verification, and JWT generation."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserUpdate, TokenResponse, UserResponse


class AuthService:
    """Service handling user authentication and registration workflows."""

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user account with a hashed password."""
        existing = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists"
            )

        hashed = hash_password(user_in.password)
        new_user = User(
            name=user_in.name.strip(),
            email=user_in.email.lower().strip(),
            password_hash=hashed
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> User:
        """Authenticate user credentials against stored bcrypt hash."""
        user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email address or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email address or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user

    @staticmethod
    def update_user(db: Session, user: User, user_in: "UserUpdate") -> User:
        """Update authenticated user profile information."""
        if user_in.name is not None and user_in.name.strip():
            user.name = user_in.name.strip()
        if user_in.email is not None and user_in.email.strip():
            new_email = user_in.email.lower().strip()
            if new_email != user.email:
                existing = db.query(User).filter(User.email == new_email).first()
                if existing and existing.id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An account with this email address already exists"
                    )
                user.email = new_email
        if user_in.password is not None and len(user_in.password) >= 8:
            user.password_hash = hash_password(user_in.password)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def generate_token_response(cls, user: User) -> TokenResponse:
        """Generate JWT access token and bundle with public user profile."""
        token = create_access_token(subject=user.id, extra_claims={"email": user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
