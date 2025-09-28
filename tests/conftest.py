import os
import uuid
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.type_api import TypeDecorator
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

os.environ["TESTING"] = "true"

from app.main import app
from app.config.database import Base, get_db
from app.models.user import User, UserRole  
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.review import Review
from app.core.security import get_password_hash


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses SQLite's CHAR type for SQLite databases.
    """
    impl = CHAR(32)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value.hex
        if isinstance(value, str):
            try:
                return uuid.UUID(value).hex
            except ValueError:
                return value
        return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str) and len(value) == 32:
            try:
                return uuid.UUID(hex=value)
            except ValueError:
                return value
        return value


def configure_sqlite_uuid():
    """Configure SQLite to handle UUID types"""
    # Override UUID type for SQLite specifically
    def _compile_uuid(element, compiler, **kw):
        return "CHAR(32)"
    
    # Register UUID compiler for SQLite
    sqlite.base.SQLiteTypeCompiler.visit_UUID = _compile_uuid


@pytest.fixture(scope="session")
def test_db():
    """Create a test database and tables"""
    # Configure SQLite UUID support
    configure_sqlite_uuid()
    
    # Create test database
    engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
    
    # Create tables  
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
def db_session(test_db):
    """Create a database session for testing"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()  # Roll back any changes
        session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use context manager for proper cleanup
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user for authentication tests"""
    # Use a unique email for each test
    email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid.uuid4(),
        name="Test User", 
        email=email,
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.USER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def test_admin(db_session):
    """Create a test admin user"""
    # Use a unique email for each test
    email = f"testadmin_{uuid.uuid4().hex[:8]}@example.com"
    admin = User(
        id=uuid.uuid4(),
        name="Test Admin",
        email=email,
        password_hash=get_password_hash("adminpassword123"),
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_service(db_session):
    """Create a test service"""
    service = Service(
        id=uuid.uuid4(),
        title="Test Service",
        description="A test service",
        price=100.00,
        duration_minutes=60,
        is_active=True
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def user_token(client, test_user):
    """Get JWT token for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "testpassword123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, test_admin):
    """Get JWT token for test admin"""
    response = client.post(
        "/api/v1/auth/login", 
        json={"email": test_admin.email, "password": "adminpassword123"}
    )
    return response.json()["access_token"]