from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from ..db import AsyncSession, get_session
from ..models import User
from ..schemas.users import UserCreationScheme, UserResponseScheme
from ..tags import Tags
from ..utils import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    check_email_deliverable,
)

router = APIRouter(prefix="/api/users")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    tags=[Tags.users.value],
    summary="Register a new user",
    description="Reigster a new user. Pass your real email address!",
    response_model=UserResponseScheme,
)
async def register_user(
    user_scheme: UserCreationScheme, db: AsyncSession = Depends(get_session)
) -> UserResponseScheme:
    """Function create a new user"""

    if not await check_email_deliverable(email=user_scheme.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is invalid. Try another one",
        )

    user = await db.execute(select(User).where(User.email == user_scheme.email))
    if user.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Account already exists"
        )

    if user_scheme.password != user_scheme.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords don`t match"
        )
    user = User(email=user_scheme.email, password=hash_password(user_scheme.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    tags=[Tags.users.value],
    summary="Login user",
    description="Login user",
)
async def login_user(
    db: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict:
    """Function login a new user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password"
    )

    user = await db.execute(select(User).where(User.email == form_data.username))

    try:
        user = user.scalar_one()
    except NoResultFound:
        user = None

    if user is None:
        raise credentials_exception

    hashed_password = user.password

    if not verify_password(form_data.password, hashed_password):
        raise credentials_exception

    access_token = create_access_token(user.email)

    return {"access_token": access_token}


@router.get(
    "/current_user",
    status_code=status.HTTP_200_OK,
    tags=[Tags.users.value],
    summary="Get current logged in user",
    description="Get current logged in user",
    response_model=UserResponseScheme,
)
async def current_user(user: User = Depends(get_current_user)) -> UserResponseScheme:
    """Function return a current logged in user"""
    return user
