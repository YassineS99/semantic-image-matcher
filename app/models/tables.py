from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, JSON, Boolean, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), unique=True, nullable=False)
    filepath = Column(String(500), nullable=False)
    uploaded_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class ImageTagRow(Base):
    __tablename__ = "image_tags"

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    attributes = Column(JSON, nullable=False)
    caption = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    classified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class ApiCallLog(Base):
    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True)
    call_type = Column(String(20), nullable=False)
    reference_id = Column(Integer, nullable=True)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)