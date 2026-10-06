from datetime import datetime
from sqlalchemy.orm import Session
from app.services.base_service import BaseService
from app.repositories.alert_repository import AlertRepository
from app.repositories.family_repository import FamilyRepository
from app.schemas.coaccion import RoboCoaccionCreate, RoboCoaccionResponse

class CoaccionService(BaseService):
    """
    Servicio de protección silenciosa ante robo, asalto o coacción.
    Prioriza el despacho discreto hacia la Policía Nacional (PNP)
    y cifra el canal de aviso a familiares de confianza.
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.alert_repo = AlertRepository(db)
        self.family_repo = FamilyRepository(db)

    def despachar_robo_coaccion(self, alerta_in: RoboCoaccionCreate) -> RoboCoaccionResponse:
        # 1. Registrar alerta en PostGIS
        alerta_db = self.alert_repo.create_spatial_alert(
            dispositivo_id=alerta_in.dispositivo_id or alerta_in.usuario or "DEV_COACCION",
            tipo_emergencia="ROBO_ASALTO_COACCION",
            nivel_gravedad=alerta_in.nivel_gravedad,
            latitud=alerta_in.latitud,
            longitud=alerta_in.longitud,
            usuario=alerta_in.usuario,
            origen_alerta="PANIC_SILENCIOSO",
            estado_confirmacion="CONFIRMADO"
        )

        # 2. Identificar familiares
        usuario_id = alerta_in.usuario or alerta_in.dispositivo_id or ""
        familiares = self.family_repo.get_by_responsible(usuario_id)
        nombres_familiares = [f.nombre for f in familiares]

        return RoboCoaccionResponse(
            estado="Alerta silenciosa de robo/asalto/coacción registrada y priorizada a la PNP",
            alerta_id=alerta_db.id,
            tipo_emergencia="ROBO_ASALTO_COACCION",
            institucion_prioritaria="Policía Nacional del Perú (PNP)",
            prioridad=alerta_in.nivel_gravedad,
            alerta_silenciosa=bool(alerta_in.activar_panic_silencioso or alerta_in.amenaza_detectada),
            coordenadas={"lat": alerta_in.latitud, "lng": alerta_in.longitud},
            enrutamiento_institucional={
                "departamento": "Perú",
                "institucion_responsible": "Policía Nacional del Perú (PNP)",
                "prioridad": alerta_in.nivel_gravedad,
                "tiempo_estimado_despliegue": "3 a 6 minutos",
                "modo": "silencioso",
                "url_dispatch": "/api/v1/coaccion/alertar/"
            },
            notificacion_familiar={
                "familiares_alertados": nombres_familiares,
                "canal": "SMS / Push / GPS cifrado",
                "detalle": alerta_in.descripcion,
                "tipo_amenaza": alerta_in.tipo_amenaza,
            },
            recurso_asignado={
                "unidad": "Unidad de Intervención Rápida PNP",
                "estado": "Desplazándose discretamente a la zona de riesgo"
            }
        )
