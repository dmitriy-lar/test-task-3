from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from ..db import AsyncSession, get_session
from ..models import Post, User
from ..redis_conf import redis_dislikes, redis_likes
from ..schemas.posts import PostCreationScheme
from ..tags import Tags
from ..utils import create_posts_response, get_current_user

router = APIRouter(prefix="/api/posts")


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    tags=[Tags.posts],
    summary="Create a new post",
    description="Create a new post",
)
async def create_post(
    post_scheme: PostCreationScheme,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Function creates a new post"""
    post = Post(**post_scheme.model_dump(), owner_id=user.id)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return await create_posts_response(posts_list=post)


@router.get(
    "/my-posts",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="List of user`s posts",
    description="Lists of user`s posts",
)
async def my_posts(
    db: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)
) -> list[dict]:
    """Function reurns all posts related to current user"""
    posts_query = await db.execute(
        select(Post).where(Post.owner_id == user.id).order_by(Post.created_at)
    )
    posts_list = posts_query.scalars().all()
    return await create_posts_response(posts_list=posts_list)


@router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="List of all posts",
    description="Lists of all posts",
)
async def list_post(
    db: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)
) -> list[dict]:
    """Function return all posts in database"""
    posts_query = await db.execute(select(Post).order_by(Post.created_at))
    posts_list = posts_query.scalars().all()
    return await create_posts_response(posts_list=posts_list)


@router.get(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="Get post by it`s id",
    description="Get post by it`s id",
)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Function returns post by passed id"""
    post_query = await db.execute(select(Post).where(Post.id == post_id))

    try:
        post = post_query.scalar_one()
    except NoResultFound:
        post = None

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found"
        )

    return await create_posts_response(posts_list=post)


@router.put(
    "/{post_id}/update",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="Update post",
    description="Update post",
)
async def update_post(
    post_id: int,
    post_scheme: PostCreationScheme,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Function updates post by passed id"""
    post_query = await db.execute(select(Post).where(Post.id == post_id))

    try:
        post = post_query.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found"
        )

    if post.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an owner of this post",
        )

    post.title = post_scheme.title
    post.description = post_scheme.description

    await db.commit()
    await db.refresh(post)
    return await create_posts_response(post)


@router.delete(
    "/{post_id}/delete",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="Delete a post",
    description="Delete a post",
)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Function deletes post by passed id"""
    post_query = await db.execute(select(Post).where(Post.id == post_id))

    try:
        post = post_query.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found"
        )

    if post.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an owner of this post",
        )

    await db.delete(post)
    await db.commit()

    return {"Message": "Post was successfully deleted"}


@router.post(
    "/add-like/{post_id}",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="Add like to a post",
    description="Add like to a post",
)
async def add_like(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Function add like to a post"""
    posts_query = await db.execute(select(Post).where(Post.id == post_id))

    try:
        post = posts_query.scalar_one()
    except NoResultFound:
        post = None

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found"
        )

    if post.owner_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner of the post cannot like it",
        )

    if post.id in map(int, await redis_likes.keys()):
        likes_count = int(await redis_likes.get(post.id))
        likes_count += 1
        await redis_likes.set(post.id, likes_count)
    else:
        await redis_likes.set(post.id, 1)
    return {"Message": "Post was successfully liked"}


@router.post(
    "/add-dislike/{post_id}",
    status_code=status.HTTP_200_OK,
    tags=[Tags.posts],
    summary="Add dislike to a post",
    description="Add dislike to a post",
)
async def add_dislike(
    post_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    """Function add dislike to a post"""
    posts_query = await db.execute(select(Post).where(Post.id == post_id))

    try:
        post = posts_query.scalar_one()
    except NoResultFound:
        post = None

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post was not found"
        )

    if post.owner_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner of the post cannot dislike it",
        )

    if post.id in map(int, await redis_dislikes.keys()):
        dislikes_count = int(await redis_dislikes.get(post.id))
        dislikes_count += 1
        await redis_dislikes.set(post.id, dislikes_count)
    else:
        await redis_dislikes.set(post.id, 1)
    return {"Message": "Post was successfully disliked"}
