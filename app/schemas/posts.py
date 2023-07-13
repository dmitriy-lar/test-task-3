from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PostBaseScheme(BaseModel):
    title: str
    description: str


class PostCreationScheme(PostBaseScheme):
    pass


class PostResponseScheme(PostBaseScheme):
    id: int
    owner_id: int
    likes_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True
