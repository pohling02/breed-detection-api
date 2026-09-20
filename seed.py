import secrets
import hashlib
from app.database import SessionLocal
from app.models.user import User
from app.models.api_key import ApiKey

def seed_data():
    db = SessionLocal()
    email = "pohling@docode.com"
    
    # 1. Check if the user already exists
    test_user = db.query(User).filter(User.email == email).first()
    
    if not test_user:
        test_user = User(email=email, is_active=True)
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Created new user: {email}")
    else:
        print(f"User {email} already exists. Generating an additional API key...")
    
    # 2. Generate a raw API key
    raw_key = f"sk_live_{secrets.token_hex(16)}"
    
    # 3. Hash the key for secure storage
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # 4. Save the hashed key to the database
    new_api_key = ApiKey(
        user_id=test_user.id,
        key_hash=key_hash,
        name="Local Development Key"
    )
    db.add(new_api_key)
    db.commit()
    
    print("\n✅ Database seeded successfully!")
    print(f"User ID: {test_user.id}")
    print(f"User Email: {test_user.email}")
    print("-" * 50)
    print("🔑 YOUR API KEY (SAVE THIS NOW):")
    print(raw_key)
    print("-" * 50)
    print("Only the hash is stored in PostgreSQL. If you lose this key, you must generate a new one.\n")
    
    db.close()

if __name__ == "__main__":
    seed_data()