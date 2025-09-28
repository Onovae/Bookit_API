from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.config.database import get_db
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.services.service_service import ServiceService
from app.core.auth import require_admin
from app.models.user import User

router = APIRouter(prefix="/services", tags=["services"])

@router.get("/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    service_service = ServiceService(db)
    return service_service.get_services()

@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: UUID, db: Session = Depends(get_db)):
    service_service = ServiceService(db)
    return service_service.get_service(service_id)

@router.post("/", response_model=ServiceResponse)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    service_service = ServiceService(db)
    return service_service.create_service(service_data)

@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: UUID,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    service_service = ServiceService(db)
    return service_service.update_service(service_id, service_update)

@router.delete("/{service_id}")
def delete_service(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    service_service = ServiceService(db)
    service_service.delete_service(service_id)
    return {"message": "Service deleted"}