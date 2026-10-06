from sqlalchemy import Column, Integer, String, DateTime, Boolean
from geoalchemy2 import Geometry
from datetime import datetime
from app.db.base import Base

class AlertaEmergencia(Base):
    __tablename__ = "alertas_emergencia"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dispositivo_id = Column(String(100), index=True, nullable=False)
    tipo_emergencia = Column(String(150), nullable=False)
    nivel_gravedad = Column(Integer, nullable=True)
    
    # Campo espacial nativo de PostGIS (SRID 4326 - WGS84 Coordenadas Geográficas)
    ubicacion = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    timestamp_dispositivo = Column(DateTime, default=datetime.utcnow, nullable=False)
    sincronizado = Column(Boolean, default=True, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=True)
