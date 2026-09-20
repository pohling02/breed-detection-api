from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class ApiUsage(Base):
    __tablename__ = "api_usages"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
 
    endpoint = Column(String, index=True, nullable=False)

    status_code = Column(Integer, nullable=False)

    response_time_ms = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    api_key = relationship("ApiKey", back_populates="api_usages")