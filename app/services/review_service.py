from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional
from uuid import UUID

from app.models.review import Review
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate

class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_review(self, review_id: UUID, user: Optional[User] = None) -> Review:
        query = self.db.query(Review).filter(Review.id == review_id)
        
        review = query.first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        if user:
            from app.models.user import UserRole
            if user.role != UserRole.ADMIN:
                booking = self.db.query(Booking).filter(Booking.id == review.booking_id).first()
                if not booking or booking.user_id != user.id:
                    raise HTTPException(status_code=404, detail="Review not found")
        
        return review

    def get_service_reviews(self, service_id: UUID) -> List[Review]:
        reviews = self.db.query(Review).join(Booking).filter(
            Booking.service_id == service_id
        ).all()
        
        return reviews

    def create_review(self, review_data: ReviewCreate, user: User) -> Review:
        booking = self.db.query(Booking).filter(
            Booking.id == review_data.booking_id,
            Booking.user_id == user.id
        ).first()
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if booking.status != BookingStatus.COMPLETED:
            raise HTTPException(status_code=422, detail="Can only review completed bookings")
        
        existing_review = self.db.query(Review).filter(
            Review.booking_id == review_data.booking_id
        ).first()
        
        if existing_review:
            raise HTTPException(status_code=409, detail="Review already exists for this booking")
        
        if not (1 <= review_data.rating <= 5):
            raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")
        
        review = Review(
            booking_id=review_data.booking_id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        return review

    def update_review(self, review_id: UUID, review_update: ReviewUpdate, user: User) -> Review:
        review = self.get_review(review_id)
        
        from app.models.user import UserRole
        booking = self.db.query(Booking).filter(Booking.id == review.booking_id).first()
        
        is_owner = booking and booking.user_id == user.id
        is_admin = user.role == UserRole.ADMIN
        
        if not (is_owner or is_admin):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        update_data = review_update.model_dump(exclude_unset=True)
        
        if 'rating' in update_data:
            if not (1 <= update_data['rating'] <= 5):
                raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")
        
        for field, value in update_data.items():
            setattr(review, field, value)
        
        self.db.commit()
        self.db.refresh(review)
        
        return review

    def delete_review(self, review_id: UUID, user: User) -> bool:
        review = self.get_review(review_id)
        
        from app.models.user import UserRole
        booking = self.db.query(Booking).filter(Booking.id == review.booking_id).first()
        
        is_owner = booking and booking.user_id == user.id
        is_admin = user.role == UserRole.ADMIN
        
        if not (is_owner or is_admin):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        self.db.delete(review)
        self.db.commit()
        
        return True

    def get_user_reviews(self, user: User) -> List[Review]:
        reviews = self.db.query(Review).join(Booking).filter(
            Booking.user_id == user.id
        ).all()
        
        return reviews