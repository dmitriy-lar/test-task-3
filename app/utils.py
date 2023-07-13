from datetime import datetime, timedelta
from typing import Any, Union
import aiohttp
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from .config import config_env
from .db import AsyncSession, get_session
from .models import User
from .redis_conf import redis_likes, redis_dislikes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login", scheme_name="JWT")


def hash_password(password: str) -> str:
    """Function return hashed password"""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Function checks if hashed and regular password match"""
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    """Function creates an access token"""
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=float(config_env["ACCESS_TOKEN_EXPIRE_MINUTES"])
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, config_env["JWT_SECRET_KEY"], config_env["ALGORITHM"]
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)
) -> dict:
    """Function returns a current logged in user"""
    try:
        payload = jwt.decode(
            token, config_env["JWT_SECRET_KEY"], algorithms=[config_env["ALGORITHM"]]
        )
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token is expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db.execute(select(User).where(User.email == username))
    try:
        user = user.scalar_one()
    except NoResultFound:
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def check_email_deliverable(email: str) -> bool:
    """Function verifies if passed email is deliverable"""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={config_env['EMAIL_HUNTER_API_KEY']}"
        ) as resp:
            resp_json = await resp.json()
            if resp_json["data"]["result"] == "deliverable":
                return True
            return False


async def create_posts_response(posts_list: list) -> Union[list[dict], dict]:
    """Function generates a response of a passed object list"""
    if isinstance(posts_list, list):
        response = []
        for item in posts_list:
            if item.id in map(int, await redis_likes.keys()):
                likes = int(await redis_likes.get(item.id))
            else:
                likes = 0
            if item.id in map(int, await redis_dislikes.keys()):
                dislikes = int(await redis_dislikes.get(item.id))
            else:
                dislikes = 0
            response.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "likes": likes,
                    "dislikes": dislikes,
                    "owner": item.owner_id,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
            )
        return response
    if posts_list.id in map(int, await redis_likes.keys()):
        likes = int(await redis_likes.get(posts_list.id))
    else:
        likes = 0
    if posts_list.id in map(int, await redis_dislikes.keys()):
        dislikes = int(await redis_dislikes.get(posts_list.id))
    else:
        dislikes = 0
    return {
        "id": posts_list.id,
        "title": posts_list.title,
        "description": posts_list.description,
        "likes": likes,
        "dislikes": dislikes,
        "owner": posts_list.owner_id,
        "created_at": posts_list.created_at,
        "updated_at": posts_list.updated_at,
    }
