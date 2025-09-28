from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ReviewBase(BaseModel):
    booking_id: UUID
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

class ReviewResponse(ReviewBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True
