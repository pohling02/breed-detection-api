from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
import hashlib

from app.database import get_db
from app.models.api_key import ApiKey
from app.utils import generate_secure_api_key
from app.schemas.api_key import KeyCreateRequest

router = APIRouter()


@router.post("/generate", summary="Generate a new API Key")
def create_api_key(request: KeyCreateRequest, db: Session = Depends(get_db)):
    new_key_string = generate_secure_api_key()
    hashed_key = hashlib.sha256(new_key_string.encode()).hexdigest()
    
    # PASS request.user_id to the database model
    new_key_record = ApiKey(
        user_id=request.user_id,
        key_hash=hashed_key,
        name=request.name,
        created_at=datetime.now(timezone.utc),
        is_active=True
    )
    
    db.add(new_key_record)
    db.commit()
    db.refresh(new_key_record)
    
    return {
        "message": "API key generated successfully.",
        "name": new_key_record.name,
        "user_id": new_key_record.user_id,
        "api_key": new_key_string,
        "warning": "Please copy this key now. For security reasons, you will not be able to view it again."
    }