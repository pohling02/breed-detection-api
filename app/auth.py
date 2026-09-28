import os
import hashlib
from fastapi import HTTPException, Security, Depends, Header
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.api_key import ApiKey
from app.models.api_usage import ApiUsage

# FIX 1: Renamed this variable to 'api_key_scheme' so it does not clash
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_valid_api_key(
    api_key_header: str = Security(api_key_scheme),
    db: Session = Depends(get_db)
) -> ApiKey:
    print(f"=== DEBUG RAW KEY ===: {repr(api_key_header)}", flush=True)
    if not api_key_header:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
    
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash, 
        ApiKey.is_active == True
    ).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="This is an invalid API Key !!!!")
    print(f"=== DEBUG HASH ===: {key_hash}", flush=True)
    return api_key

def verify_rate_limit(
    api_key: ApiKey = Depends(get_valid_api_key),
    db: Session = Depends(get_db)
) -> ApiKey:
    one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
    
    recent_requests = db.query(ApiUsage).filter(
        ApiUsage.api_key_id == api_key.id,
        ApiUsage.created_at >= one_minute_ago
    ).count()

    if recent_requests >= 5:
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. Maximum 5 requests per minute."
        )
    
    return api_key