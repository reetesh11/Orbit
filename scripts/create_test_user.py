"""Create a test user for development."""
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import User, UserProfile, SharedContext


def create_test_user(email: str = "test@example.com", phone: str = "+1234567890"):
    """Create a test user."""
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing = db.query(User).filter(
            (User.email == email) | (User.phone == phone)
        ).first()
        
        if existing:
            print(f"User already exists: {existing.id}")
            return existing.id
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=email,
            phone=phone,
            status="active",
        )
        db.add(user)
        db.flush()
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            profile={"name": "Test User"},
        )
        db.add(profile)
        
        # Create shared context
        shared_context = SharedContext(
            user_id=user.id,
            context={},
        )
        db.add(shared_context)
        
        db.commit()
        print(f"Created test user: {user.id}")
        return user.id
    except Exception as e:
        db.rollback()
        print(f"Error creating test user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="test@example.com")
    parser.add_argument("--phone", default="+1234567890")
    args = parser.parse_args()
    
    create_test_user(email=args.email, phone=args.phone)
