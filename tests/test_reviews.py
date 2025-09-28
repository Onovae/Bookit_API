import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime, timedelta
from app.models.booking import Booking, BookingStatus

class TestReviewSystem:
    """Test review creation and business logic"""
    
    @pytest.fixture
    def completed_booking(self, db_session, test_user, test_service):
        """Create a completed booking for review testing"""
        booking = Booking(
            id=uuid4(),
            user_id=test_user.id,
            service_id=test_service.id,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now() - timedelta(days=1) + timedelta(hours=1),
            status=BookingStatus.COMPLETED
        )
        db_session.add(booking)
        db_session.commit()
        return booking
    
    def test_create_review_success(self, client, user_token, completed_booking):
        """Test successful review creation"""
        review_data = {
            "booking_id": str(completed_booking.id),
            "rating": 5,
            "comment": "Excellent service!"
        }
        
        response = client.post(
            "/api/v1/reviews/",
            headers={"Authorization": f"Bearer {user_token}"},
            json=review_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == review_data["comment"]
        assert "id" in data
    
    def test_create_review_booking_not_completed(self, client, user_token, test_user, test_service, db_session):
        """Test review creation fails for non-completed booking (422)"""
        # Create pending booking
        pending_booking = Booking(
            id=uuid4(),
            user_id=test_user.id,
            service_id=test_service.id,
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1) + timedelta(hours=1),
            status=BookingStatus.PENDING
        )
        db_session.add(pending_booking)
        db_session.commit()
        
        review_data = {
            "booking_id": str(pending_booking.id),
            "rating": 5,
            "comment": "Premature review"
        }
        
        response = client.post(
            "/api/v1/reviews/",
            headers={"Authorization": f"Bearer {user_token}"},
            json=review_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "completed" in response.json()["detail"].lower()
    
    def test_create_review_not_own_booking(self, client, completed_booking, db_session):
        """Test user cannot review booking they didn't make (403)"""
        # Create different user
        from app.models.user import User, Role
        from app.core.security import get_password_hash
        
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Other User",
            role=Role.USER
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Login as other user
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "other@example.com", "password": "password123"}
        )
        other_token = login_response.json()["access_token"]
        
        review_data = {
            "booking_id": str(completed_booking.id),
            "rating": 1,
            "comment": "Unauthorized review attempt"
        }
        
        response = client.post(
            "/api/v1/reviews/",
            headers={"Authorization": f"Bearer {other_token}"},
            json=review_data
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_duplicate_review(self, client, user_token, completed_booking, db_session):
        """Test user cannot create multiple reviews for same booking (409)"""
        # Create first review
        from app.models.review import Review
        
        existing_review = Review(
            id=uuid4(),
            booking_id=completed_booking.id,
            rating=4,
            comment="First review"
        )
        db_session.add(existing_review)
        db_session.commit()
        
        # Try to create second review
        review_data = {
            "booking_id": str(completed_booking.id),
            "rating": 5,
            "comment": "Duplicate review attempt"
        }
        
        response = client.post(
            "/api/v1/reviews/",
            headers={"Authorization": f"Bearer {user_token}"},
            json=review_data
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already" in response.json()["detail"].lower()
    
    def test_get_reviews_for_service(self, client, test_service, completed_booking, db_session):
        """Test retrieving reviews for a service"""
        # Create review
        from app.models.review import Review
        
        review = Review(
            id=uuid4(),
            booking_id=completed_booking.id,
            rating=5,
            comment="Great service!"
        )
        db_session.add(review)
        db_session.commit()
        
        response = client.get(f"/api/v1/services/{test_service.id}/reviews")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(review_data["rating"] == 5 for review_data in data)
    
    def test_get_user_reviews(self, client, user_token, completed_booking, db_session):
        """Test user can get their own reviews"""
        # Create review
        from app.models.review import Review
        
        review = Review(
            id=uuid4(),
            booking_id=completed_booking.id,
            rating=5,
            comment="My review"
        )
        db_session.add(review)
        db_session.commit()
        
        response = client.get(
            "/api/v1/users/me/reviews",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(review_data["comment"] == "My review" for review_data in data)
    
    def test_review_rating_validation(self, client, user_token, completed_booking):
        """Test review rating must be between 1-5"""
        invalid_ratings = [0, 6, -1, 10]
        
        for rating in invalid_ratings:
            review_data = {
                "booking_id": str(completed_booking.id),
                "rating": rating,
                "comment": f"Invalid rating {rating}"
            }
            
            response = client.post(
                "/api/v1/reviews/",
                headers={"Authorization": f"Bearer {user_token}"},
                json=review_data
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_review_success(self, client, user_token, completed_booking, db_session):
        """Test user can update their own review"""
        # Create review
        from app.models.review import Review
        
        review = Review(
            id=uuid4(),
            booking_id=completed_booking.id,
            rating=3,
            comment="Initial review"
        )
        db_session.add(review)
        db_session.commit()
        
        update_data = {
            "rating": 5,
            "comment": "Updated review - much better!"
        }
        
        response = client.put(
            f"/api/v1/reviews/{review.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == update_data["comment"]
    
    def test_delete_review_admin_success(self, client, admin_token, completed_booking, db_session):
        """Test admin can delete any review (204)"""
        # Create review
        from app.models.review import Review
        
        review = Review(
            id=uuid4(),
            booking_id=completed_booking.id,
            rating=1,
            comment="Bad review to delete"
        )
        db_session.add(review)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/reviews/{review.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT