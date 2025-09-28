from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ServiceBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    duration_minutes: int
    is_active: Optional[bool] = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None

class ServiceResponse(ServiceBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True
