from fastapi import FastAPI
from app.db import engine, Base
from app.routers import users, posts

app = FastAPI(title="Social Network App")

# Include routers
app.include_router(users.router)
app.include_router(posts.router)


@app.on_event("startup")
async def startup():
    """Initiate tables in database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
