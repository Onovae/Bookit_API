import pytest
from datetime import datetime, timedelta
from fastapi import status
from uuid import uuid4
from app.models.booking import Booking, BookingStatus

class TestBookingConflicts:
    """Test booking conflict detection and prevention"""
    
    def test_create_booking_success(self, client, user_token, test_service):
        """Test successful booking creation"""
        start_time = datetime.now() + timedelta(days=1)
        
        response = client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "service_id": str(test_service.id),
                "start_time": start_time.isoformat(),
                "end_time": (start_time + timedelta(hours=1)).isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_booking_conflict_prevention(self, client, db_session, test_user, test_service):
        """Test that overlapping bookings are prevented with 409 Conflict"""
        # Create first booking
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        existing_booking = Booking(
            id=uuid4(),
            user_id=test_user.id,
            service_id=test_service.id,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CONFIRMED
        )
        db_session.add(existing_booking)
        db_session.commit()
        
        # Login and get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        
        # Try to create overlapping booking
        overlapping_start = start_time + timedelta(minutes=30)  # Overlaps with existing
        overlapping_end = overlapping_start + timedelta(hours=1)
        
        response = client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "service_id": str(test_service.id),
                "start_time": overlapping_start.isoformat(),
                "end_time": overlapping_end.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "conflict" in response.json()["detail"].lower()
    
    def test_booking_no_conflict_different_times(self, client, db_session, test_user, test_service):
        """Test that non-overlapping bookings are allowed"""
        # Create first booking
        start_time1 = datetime.now() + timedelta(days=1)
        end_time1 = start_time1 + timedelta(hours=1)
        
        existing_booking = Booking(
            id=uuid4(),
            user_id=test_user.id,
            service_id=test_service.id,
            start_time=start_time1,
            end_time=end_time1,
            status=BookingStatus.CONFIRMED
        )
        db_session.add(existing_booking)
        db_session.commit()
        
        # Login and get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        
        # Create non-overlapping booking (2 hours later)
        start_time2 = end_time1 + timedelta(hours=1)  # No overlap
        end_time2 = start_time2 + timedelta(hours=1)
        
        response = client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "service_id": str(test_service.id),
                "start_time": start_time2.isoformat(),
                "end_time": end_time2.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_booking_past_time_validation(self, client, user_token, test_service):
        """Test that bookings in the past are rejected"""
        past_time = datetime.now() - timedelta(hours=1)
        
        response = client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "service_id": str(test_service.id),
                "start_time": past_time.isoformat(),
                "end_time": (past_time + timedelta(hours=1)).isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "past" in response.json()["detail"].lower()
    
    def test_booking_duration_validation(self, client, user_token, test_service):
        """Test that booking duration must match service duration"""
        start_time = datetime.now() + timedelta(days=1)
        # Service duration is 60 minutes, but booking for 30 minutes
        wrong_end_time = start_time + timedelta(minutes=30)
        
        response = client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "service_id": str(test_service.id),
                "start_time": start_time.isoformat(),
                "end_time": wrong_end_time.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "duration" in response.json()["detail"].lower()