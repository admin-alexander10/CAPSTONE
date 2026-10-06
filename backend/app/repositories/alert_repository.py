from typing import List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.elements import WKTElement
from app.repositories.base_repository import BaseRepository
from app.domain.interfaces.repositories import IAlertRepository
from app.models.alert import AlertaEmergencia

class AlertRepository(BaseRepository[AlertaEmergencia], IAlertRepository):
    """Repositorio geoespacial especializado en PostgreSQL / PostGIS."""

    def __init__(self, db: Session):
        super().__init__(db, AlertaEmergencia)

    def create_spatial_alert(
        self,
        dispositivo_id: str,
        tipo_emergencia: str,
        nivel_gravedad: int,
        latitud: float,
        longitud: float,
        usuario: Optional[str] = None,
        origen_alerta: str = "MANUAL",
        estado_confirmacion: str = "CONFIRMADO"
    ) -> AlertaEmergencia:
        """Inserta punto espacial POINT(longitud latitud) en SRID 4326."""
        punto_wkt = f"POINT({longitud} {latitud})"
        ubicacion_geo = WKTElement(punto_wkt, srid=4326)

        nueva_alerta = AlertaEmergencia(
            dispositivo_id=dispositivo_id or "DEV_GENERIC",
            tipo_emergencia=tipo_emergencia,
            nivel_gravedad=nivel_gravedad,
            ubicacion=ubicacion_geo,
            timestamp_dispositivo=datetime.utcnow(),
            sincronizado=True,
            creado_en=datetime.utcnow()
        )
        return self.create(nueva_alerta)

    def get_active_alerts_with_coords(self, limit: int = 50) -> List[Tuple[AlertaEmergencia, float, float]]:
        """Extrae la entidad junto con latitud y longitud calculadas por PostGIS (ST_Y, ST_X)."""
        return self.db.query(
            AlertaEmergencia,
            func.ST_Y(AlertaEmergencia.ubicacion).label('latitud'),
            func.ST_X(AlertaEmergencia.ubicacion).label('longitud')
        ).order_by(AlertaEmergencia.id.desc()).limit(limit).all()

    def get_active_alerts(self, limit: int = 50) -> List[Any]:
        return self.get_active_alerts_with_coords(limit=limit)

    def get_alerts_in_radius(self, lat: float, lng: float, radius_km: float) -> List[Tuple[AlertaEmergencia, float, float]]:
        """Consulta geoespacial de proximidad usando buffer PostGIS."""
        punto_centro = WKTElement(f"POINT({lng} {lat})", srid=4326)
        # ST_DWithin con cast a geografía para distancia en metros
        return self.db.query(
            AlertaEmergencia,
            func.ST_Y(AlertaEmergencia.ubicacion).label('latitud'),
            func.ST_X(AlertaEmergencia.ubicacion).label('longitud')
        ).filter(
            func.ST_DWithin(
                func.cast(AlertaEmergencia.ubicacion, func.Geometry),
                punto_centro,
                radius_km / 111.32 # Aproximación en grados
            )
        ).order_by(AlertaEmergencia.id.desc()).all()
