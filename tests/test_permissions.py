import pytest
from fastapi import status
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus
from app.core.security import get_password_hash
from uuid import uuid4
from datetime import datetime, timedelta

class TestAuthorization:
    """Test role-based access control and permissions"""
    
    def test_user_cannot_access_admin_endpoints(self, client, user_token):
        """Test that regular users cannot access admin-only endpoints"""
        # Try to create a service (admin only)
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "title": "Test Service",
                "description": "Test description",
                "price": 100.0,
                "duration_minutes": 60
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_access_admin_endpoints(self, client, admin_token):
        """Test that admin users can access admin endpoints"""
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "Admin Service",
                "description": "Admin created service",
                "price": 150.0,
                "duration_minutes": 90
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_user_can_only_see_own_bookings(self, client, db_session, test_user, test_service):
        """Test that users can only see their own bookings"""
        # Create another user and booking
        other_user = User(
            id=uuid4(),
            name="Other User", 
            email="other@example.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.USER
        )
        db_session.add(other_user)
        
        other_booking = Booking(
            id=uuid4(),
            user_id=other_user.id,
            service_id=test_service.id,
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=1),
            status=BookingStatus.CONFIRMED
        )
        db_session.add(other_booking)
        db_session.commit()
        
        # Login as test_user
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        
        # Get bookings - should only see own bookings (none in this case)
        response = client.get(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        bookings = response.json()
        assert len(bookings) == 0  # Should not see other user's booking
    
    def test_admin_can_see_all_bookings(self, client, admin_token, db_session, test_user, test_service):
        """Test that admin can see all bookings"""
        # Create a booking for test_user
        booking = Booking(
            id=uuid4(),
            user_id=test_user.id,
            service_id=test_service.id,
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=1),
            status=BookingStatus.PENDING
        )
        db_session.add(booking)
        db_session.commit()
        
        # Admin should see all bookings
        response = client.get(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        bookings = response.json()
        assert len(bookings) >= 1  # Should see the created booking