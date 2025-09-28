from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.config.database import get_db
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse
from app.services.booking_service import BookingService
from app.core.auth import get_current_active_user, require_admin
from app.models.user import User, UserRole

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking_service = BookingService(db)
    return booking_service.create_booking(booking_data, current_user)

@router.get("/", response_model=List[BookingResponse])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking_service = BookingService(db)
    user_filter = None if current_user.role == UserRole.ADMIN else current_user
    return booking_service.get_bookings(user=user_filter)

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking_service = BookingService(db)
    user_filter = None if current_user.role == UserRole.ADMIN else current_user
    return booking_service.get_booking(booking_id, user_filter)

@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: UUID,
    booking_update: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking_service = BookingService(db)
    return booking_service.update_booking(booking_id, booking_update, current_user)

@router.delete("/{booking_id}")
def delete_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking_service = BookingService(db)
    booking_service.delete_booking(booking_id, current_user)
    return {"message": "Booking deleted"}