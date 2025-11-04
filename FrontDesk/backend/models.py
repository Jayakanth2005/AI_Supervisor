# backend/models.py
# from sqlalchemy import Column, String, Text, DateTime, Enum
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.ext.declarative import declarative_base
# import enum, uuid, datetime

# Base = declarative_base()

# class RequestStatus(str, enum.Enum):
#     PENDING = "PENDING"
#     RESOLVED = "RESOLVED"
#     UNRESOLVED = "UNRESOLVED"

# class HelpRequest(Base):
#     __tablename__ = "help_requests"
#     id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     caller_id = Column(String, nullable=False)
#     question = Column(Text, nullable=False)
#     status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#     resolved_at = Column(DateTime, nullable=True)
#     supervisor_response = Column(Text, nullable=True)
#     timeout_at = Column(DateTime, nullable=True)
#     source_room = Column(String, nullable=True)

# class KnowledgeBase(Base):
#     __tablename__ = "knowledge_base"
#     id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     question_pattern = Column(String, unique=True, nullable=False)
#     answer = Column(Text, nullable=False)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#     source = Column(String, default="SEED")


from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


# ------------------------------
# Help Request Model
# ------------------------------
class HelpRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    caller_name: str
    question: str
    status: str = Field(default="pending")  # pending / resolved / unresolved
    supervisor_response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    livekit_room: Optional[str] = None
    follow_up_sent: bool = Field(default=False)


# ------------------------------
# Knowledge Base Model
# ------------------------------
class KnowledgeBase(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    question_pattern: str
    answer: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="SEED")
