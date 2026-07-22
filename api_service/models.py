from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .database import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    uses = Column(Integer, default=0)

class DownloadJob(Base):
    __tablename__ = "download_jobs"

    id = Column(String, primary_key=True, index=True) # UUID
    url = Column(String, nullable=False)
    status = Column(String, default="pending") # pending, downloading, completed, error
    progress = Column(Integer, default=0)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(String, nullable=True)

