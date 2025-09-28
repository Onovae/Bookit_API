import pytest
from fastapi import status
from uuid import uuid4

class TestServiceManagement:
    """Test service CRUD operations and business logic"""
    
    def test_create_service_admin_success(self, client, admin_token):
        """Test admin can create new service"""
        service_data = {
            "name": "Test Service",
            "description": "Test service description",
            "price": 50.00,
            "duration_minutes": 30,
            "category": "Test Category"
        }
        
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=service_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == service_data["name"]
        assert data["price"] == service_data["price"]
        assert data["is_active"] is True  # Default value
    
    def test_create_service_user_forbidden(self, client, user_token):
        """Test regular user cannot create service (403 Forbidden)"""
        service_data = {
            "name": "Test Service",
            "description": "Test service description",
            "price": 50.00,
            "duration_minutes": 30,
            "category": "Test Category"
        }
        
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {user_token}"},
            json=service_data
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_services_public_access(self, client, test_service):
        """Test anyone can view services list"""
        response = client.get("/api/v1/services/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(service["id"] == str(test_service.id) for service in data)
    
    def test_get_service_by_id(self, client, test_service):
        """Test get single service by ID"""
        response = client.get(f"/api/v1/services/{test_service.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_service.id)
        assert data["name"] == test_service.name
    
    def test_get_service_not_found(self, client):
        """Test 404 for non-existent service"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/services/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_service_admin_success(self, client, admin_token, test_service):
        """Test admin can update service"""
        update_data = {
            "name": "Updated Service Name",
            "price": 75.00
        }
        
        response = client.put(
            f"/api/v1/services/{test_service.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
    
    def test_update_service_user_forbidden(self, client, user_token, test_service):
        """Test regular user cannot update service"""
        update_data = {"name": "Hacked Service"}
        
        response = client.put(
            f"/api/v1/services/{test_service.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_service_admin_success(self, client, admin_token, test_service):
        """Test admin can delete service (204 No Content)"""
        response = client.delete(
            f"/api/v1/services/{test_service.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify service is deleted
        get_response = client.get(f"/api/v1/services/{test_service.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_service_user_forbidden(self, client, user_token, test_service):
        """Test regular user cannot delete service"""
        response = client.delete(
            f"/api/v1/services/{test_service.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_service_filtering_by_category(self, client, db_session, test_service):
        """Test service filtering by category"""
        # Create service with different category
        from app.models.service import Service
        from uuid import uuid4
        
        other_service = Service(
            id=uuid4(),
            name="Other Service",
            description="Different category service",
            price=30.0,
            duration_minutes=45,
            category="Other Category"
        )
        db_session.add(other_service)
        db_session.commit()
        
        # Filter by test service category
        response = client.get(f"/api/v1/services/?category={test_service.category}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return services with matching category
        assert all(service["category"] == test_service.category for service in data)
    
    def test_service_validation_negative_price(self, client, admin_token):
        """Test service creation with invalid negative price"""
        service_data = {
            "name": "Invalid Service",
            "description": "Service with negative price",
            "price": -10.00,  # Invalid
            "duration_minutes": 30,
            "category": "Test"
        }
        
        response = client.post(
            "/api/v1/services/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=service_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY