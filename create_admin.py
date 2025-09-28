import sys
import os
from uuid import uuid4

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_admin_user():
    """Create admin user from environment variables"""
    
    # Database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(
            User.email == settings.admin_email,
            User.role == UserRole.ADMIN
        ).first()
        
        if existing_admin:
            print(f"✅ Admin user already exists: {settings.admin_email}")
            return
        
        # Create admin user from environment variables
        admin_user = User(
            id=uuid4(),
            name=settings.admin_name,
            email=settings.admin_email,
            password_hash=get_password_hash(settings.admin_password),
            role=UserRole.ADMIN
        )
        
        db.add(admin_user)
        db.commit()
        
        print("🎉 Admin user created successfully!")
        print(f"📧 Email: {settings.admin_email}")
        print(f"👤 Name: {settings.admin_name}")
        print(f"🔑 Password: {settings.admin_password}")
        print("⚠️  IMPORTANT: Change this password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating admin user...")
    create_admin_user()