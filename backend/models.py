from sqlalchemy import Column, BigInteger, String, Integer, Boolean, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(16), default="user")
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    banned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Image(Base):
    __tablename__ = "images"
    id = Column(BigInteger, primary_key=True)
    r2_url = Column(Text, nullable=False)
    score_count = Column(Integer, default=0)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Score(Base):
    __tablename__ = "scores"
    id = Column(BigInteger, primary_key=True)
    image_id = Column(BigInteger, ForeignKey("images.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    aesthetic_score = Column(Integer, CheckConstraint("aesthetic_score BETWEEN 1 AND 10"))
    completeness_score = Column(Integer, CheckConstraint("completeness_score BETWEEN 1 AND 10"))
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditExport(Base):
    __tablename__ = "audit_exports"
    id = Column(BigInteger, primary_key=True)
    admin_id = Column(BigInteger, ForeignKey("users.id"))
    export_type = Column(String(16))
    filters = Column(JSONB)
    record_count = Column(Integer)
    exported_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
