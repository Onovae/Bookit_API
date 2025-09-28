from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from app.models.booking import Booking, BookingStatus
from app.models.service import Service
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingUpdate

class BookingService:
    def __init__(self, db: Session):
        self.db = db

    def get_booking(self, booking_id: UUID, user: Optional[User] = None) -> Booking:
        query = self.db.query(Booking).filter(Booking.id == booking_id)
        
        if user:
            from app.models.user import UserRole
            if user.role != UserRole.ADMIN:
                query = query.filter(Booking.user_id == user.id)
        
        booking = query.first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return booking

    def get_bookings(self, user: Optional[User] = None) -> List[Booking]:
        query = self.db.query(Booking)
        
        if user:
            from app.models.user import UserRole
            if user.role != UserRole.ADMIN:
                query = query.filter(Booking.user_id == user.id)
        
        return query.all()

    def create_booking(self, booking_data: BookingCreate, user: User) -> Booking:
        # Check service exists
        service = self.db.query(Service).filter(
            Service.id == booking_data.service_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Normalize datetimes to UTC for consistent comparisons
        start_time = self._normalize_datetime(booking_data.start_time)
        end_time = self._normalize_datetime(booking_data.end_time)
        now_utc = datetime.now(timezone.utc)

        # Basic validation
        if start_time >= end_time:
            raise HTTPException(status_code=422, detail="Start time must be before end time")
        
        if start_time < now_utc:
            raise HTTPException(status_code=422, detail="Cannot book in the past")
        
        # Check duration matches service
        expected_duration = service.duration_minutes
        actual_duration = (end_time - start_time).total_seconds() / 60
        
        if abs(actual_duration - expected_duration) > 5:
            raise HTTPException(status_code=422, detail=f"Booking duration must be {expected_duration} minutes")
        
        # Check for conflicts
        if self._has_conflict(booking_data.service_id, start_time, end_time):
            raise HTTPException(status_code=409, detail="Booking conflicts with existing reservation")
        
        # Create booking
        booking = Booking(
            user_id=user.id,
            service_id=booking_data.service_id,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING
        )
        
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        
        return booking

    def update_booking(self, booking_id: UUID, booking_update: BookingUpdate, user: User) -> Booking:
        booking = self.get_booking(booking_id, user)
        
        from app.models.user import UserRole
        if booking.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        update_data = booking_update.model_dump(exclude_unset=True)
        
        # Apply updates
        for field, value in update_data.items():
            setattr(booking, field, value)
        
        self.db.commit()
        self.db.refresh(booking)
        
        return booking

    def delete_booking(self, booking_id: UUID, user: User) -> bool:
        booking = self.get_booking(booking_id, user)
        
        from app.models.user import UserRole
        if booking.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        self.db.delete(booking)
        self.db.commit()
        
        return True

    def _has_conflict(self, service_id: UUID, start_time: datetime, end_time: datetime) -> bool:
        existing = self.db.query(Booking).filter(
            Booking.service_id == service_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).first()
        
        return existing is not None

    @staticmethod
    def _normalize_datetime(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)