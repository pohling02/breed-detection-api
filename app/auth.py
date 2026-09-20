import hashlib
from fastapi import HTTPException, Security, Depends, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.api_key import ApiKey

# The header name your HTML page will send
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_valid_api_key(
    api_key_header: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> ApiKey:
    if not api_key_header:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash, 
        ApiKey.is_active == True
    ).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return api_key