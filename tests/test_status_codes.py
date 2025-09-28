import pytest
from fastapi import status
from uuid import uuid4

class TestHTTPStatusCodes:
    """Test that all endpoints return correct HTTP status codes"""
    
    def test_successful_operations_status_codes(self, client, admin_token, user_token):
        """Test successful operations return correct 2xx codes"""
        
        # 200 OK - GET operations
        response = client.get("/api/v1/services/")
        assert response.status_code == status.HTTP_200_OK
        
        # 201 Created - POST operations
        service_data = {
            "name": "Status Test Service",
            "description": "Testing status codes",
            "price": 25.0,
            "duration_minutes": 30,
            "category": "Test"
        }
        
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=service_data
        )
        assert response.status_code == status.HTTP_201_CREATED
        service_id = response.json()["id"]
        
        # 200 OK - PUT operations
        response = client.put(
            f"/api/v1/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Updated Service"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 204 No Content - DELETE operations
        response = client.delete(
            f"/api/v1/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_client_error_status_codes(self, client, user_token):
        """Test client error scenarios return correct 4xx codes"""
        
        # 400 Bad Request - Invalid JSON
        response = client.post(
            "/api/v1/auth/register",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 401 Unauthorized - No authentication
        response = client.get("/api/v1/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 401 Unauthorized - Invalid token
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # 403 Forbidden - User trying to access admin endpoint
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Test",
                "description": "Test",
                "price": 50.0,
                "duration_minutes": 30,
                "category": "Test"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # 404 Not Found - Non-existent resource
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/services/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # 422 Unprocessable Entity - Validation errors
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",  # Invalid email format
                "password": "123",  # Too short
                "full_name": ""  # Empty name
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_conflict_status_codes(self, client, user_token, test_user, test_service, db_session):
        """Test conflict scenarios return 409 Conflict"""
        from datetime import datetime, timedelta
        from app.models.booking import Booking, BookingStatus
        
        # Create existing booking
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
        
        # Try to create conflicting booking
        conflicting_start = start_time + timedelta(minutes=30)
        
        response = client.post(
            "/api/v1/bookings/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "service_id": str(test_service.id),
                "start_time": conflicting_start.isoformat(),
                "end_time": (conflicting_start + timedelta(hours=1)).isoformat()
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        
        # Try to register with existing email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # Already exists
                "password": "newpassword123",
                "full_name": "New User"
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_validation_error_details(self, client):
        """Test validation errors include proper detail messages"""
        
        # Test registration with invalid data
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "123",
                "full_name": ""
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        # Validation errors should be in detail
        assert isinstance(data["detail"], (str, list))
    
    def test_authentication_error_messages(self, client):
        """Test authentication errors have appropriate messages"""
        
        # Wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()
        
        # Non-existent user
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_business_logic_errors(self, client, user_token, test_service):
        """Test business logic violations return appropriate status codes"""
        from datetime import datetime, timedelta
        
        # Booking in the past (422 Unprocessable Entity)
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
        
        # Wrong booking duration (422 Unprocessable Entity)
        start_time = datetime.now() + timedelta(days=1)
        wrong_end_time = start_time + timedelta(minutes=30)  # Service is 60 minutes
        
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
    
    def test_options_method_cors(self, client):
        """Test OPTIONS method returns 200 for CORS"""
        response = client.options("/api/v1/services/")
        # Should not error - CORS is handled by FastAPI middleware
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled