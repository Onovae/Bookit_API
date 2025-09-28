from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.booking import BookingStatus

class BookingBase(BaseModel):
    service_id: UUID
    start_time: datetime
    end_time: datetime

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[BookingStatus] = None

class BookingResponse(BookingBase):
    id: UUID
    user_id: UUID
    status: BookingStatus
    created_at: datetime
    class Config:
        from_attributes = True
