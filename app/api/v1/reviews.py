from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.config.database import get_db
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.services.review_service import ReviewService
from app.core.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new review for a completed booking."""
    review_service = ReviewService(db)
    return review_service.create_review(review_data, current_user)

@router.patch("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: UUID,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a review. Users can only update their own reviews."""
    review_service = ReviewService(db)
    return review_service.update_review(review_id, review_update, current_user)

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a review. Users can delete their own reviews, admins can delete any."""
    review_service = ReviewService(db)
    review_service.delete_review(review_id, current_user)