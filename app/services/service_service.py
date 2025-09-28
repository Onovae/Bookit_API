from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional
from uuid import UUID

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class ServiceService:
    def __init__(self, db: Session):
        self.db = db

    def get_service(self, service_id: UUID) -> Service:
        service = self.db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service

    def get_services(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        q: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        active: Optional[bool] = None
    ) -> List[Service]:
        query = self.db.query(Service)
        
        if q:
            query = query.filter(
                Service.title.ilike(f"%{q}%") | 
                Service.description.ilike(f"%{q}%")
            )
        
        if price_min is not None:
            query = query.filter(Service.price >= price_min)
            
        if price_max is not None:
            query = query.filter(Service.price <= price_max)
            
        if active is not None:
            query = query.filter(Service.is_active == active)
        
        return query.offset(skip).limit(limit).all()

    def create_service(self, service_data: ServiceCreate) -> Service:
        if service_data.price <= 0:
            raise HTTPException(status_code=422, detail="Price must be greater than 0")
        
        if service_data.duration_minutes <= 0:
            raise HTTPException(status_code=422, detail="Duration must be greater than 0")
        
        service = Service(**service_data.model_dump())
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        
        return service

    def update_service(self, service_id: UUID, service_update: ServiceUpdate) -> Service:
        service = self.get_service(service_id)
        
        update_data = service_update.model_dump(exclude_unset=True)
        
        if 'price' in update_data and update_data['price'] <= 0:
            raise HTTPException(status_code=422, detail="Price must be greater than 0")
        
        if 'duration_minutes' in update_data and update_data['duration_minutes'] <= 0:
            raise HTTPException(status_code=422, detail="Duration must be greater than 0")
        
        for field, value in update_data.items():
            setattr(service, field, value)
        
        self.db.commit()
        self.db.refresh(service)
        
        return service

    def delete_service(self, service_id: UUID) -> bool:
        service = self.get_service(service_id)
        
        from app.models.booking import Booking, BookingStatus
        active_bookings = self.db.query(Booking).filter(
            Booking.service_id == service_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).first()
        
        if active_bookings:
            raise HTTPException(status_code=422, detail="Cannot delete service with active bookings")
        
        service.is_active = False
        self.db.commit()
        
        return True

    def get_service_reviews(self, service_id: UUID) -> List:
        """Get all reviews for a service."""
        from app.models.review import Review
        from app.models.booking import Booking
        
        reviews = self.db.query(Review).join(Booking).filter(
            Booking.service_id == service_id
        ).all()
        
        return reviews