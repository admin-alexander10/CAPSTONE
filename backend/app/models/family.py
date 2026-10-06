from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base import Base

class RedFamiliar(Base):
    __tablename__ = "red_familiar"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_responsable = Column(String(100), index=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    parentesco = Column(String(80), nullable=False)
    dispositivo_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True) # Coincide con PostgreSQL
