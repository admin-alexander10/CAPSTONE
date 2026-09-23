from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from geoalchemy2 import Geometry
from database import Base
from datetime import datetime

class AlertaEmergencia(Base):
    __tablename__ = "alertas_emergencia"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dispositivo_id = Column(String(50), index=True, nullable=False)
    tipo_emergencia = Column(String(100), nullable=False)
    nivel_gravedad = Column(Integer, nullable=False)
    
    # Nuevos campos para soportar el enfoque Zero-Touch y Automatización Sismológica
    origen_alerta = Column(String(30), default="MANUAL", nullable=False) # "MANUAL" o "AUTOMATICO_INERCIA"
    estado_confirmacion = Column(String(30), default="CONFIRMADO", nullable=False) # "CONFIRMADO", "EXPIRADO_INCONSCIENTE"
    
    # Campo espacial nativo de PostGIS (SRID 4326 para coordenadas WGS84 - Lat/Lng)
    ubicacion = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    timestamp_dispositivo = Column(DateTime, default=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=True, nullable=False)