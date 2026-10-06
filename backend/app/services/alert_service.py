from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.base_service import BaseService
from app.repositories.alert_repository import AlertRepository
from app.repositories.family_repository import FamilyRepository
from app.infrastructure.gateways.notification_gateway import EmergencyNotificationGateway
from app.schemas.alert import (
    AlertaCreate,
    AlertaResponse,
    AlertaDetalle,
    EnrutamientoInstitucional,
    NotificacionFamiliar,
    RecursoAsignado
)

class AlertService(BaseService):
    """
    Servicio de orquestación de emergencias y despacho táctico:
    1. Persiste el punto espacial en PostgreSQL con PostGIS.
    2. Identifica la red familiar del usuario y despacha notificaciones.
    3. Asigna recursos de respuesta B2G (COER / Bomberos).
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.alert_repo = AlertRepository(db)
        self.family_repo = FamilyRepository(db)
        self.notification_gateway = EmergencyNotificationGateway()

    def despachar_alerta(self, alerta_in: AlertaCreate) -> AlertaResponse:
        es_critico = alerta_in.nivel_gravedad >= 4
        origen = "AUTOMATICO_INERCIA" if es_critico else "MANUAL"
        confirmacion = "EXPIRADO_INCONSCIENTE" if es_critico else "CONFIRMADO"

        # 1. Persistencia geoespacial en PostGIS
        alerta_db = self.alert_repo.create_spatial_alert(
            dispositivo_id=alerta_in.dispositivo_id or alerta_in.usuario or "DEV_GENERIC",
            tipo_emergencia=alerta_in.tipo_emergencia,
            nivel_gravedad=alerta_in.nivel_gravedad,
            latitud=alerta_in.latitud,
            longitud=alerta_in.longitud,
            usuario=alerta_in.usuario,
            origen_alerta=origen,
            estado_confirmacion=confirmacion
        )

        # 2. Búsqueda y notificación a red familiar
        usuario_id = alerta_in.usuario or alerta_in.dispositivo_id or ""
        familiares = self.family_repo.get_by_responsible(usuario_id)
        nombres_familiares = [f.nombre for f in familiares]

        notif_resultado = self.notification_gateway.notify_family_members(
            familiares=nombres_familiares,
            tipo_emergencia=alerta_in.tipo_emergencia,
            coordenadas={"lat": alerta_in.latitud, "lng": alerta_in.longitud},
            es_critico=es_critico
        )

        # 3. Asignación institucional B2G
        institucion = "Centro de Operaciones de Emergencia Regional (COER) & Bomberos B2G"
        self.notification_gateway.dispatch_institutional_alert(
            institucion=institucion,
            alerta_id=alerta_db.id,
            tipo_emergencia=alerta_in.tipo_emergencia,
            prioridad=alerta_in.nivel_gravedad,
            coordenadas={"lat": alerta_in.latitud, "lng": alerta_in.longitud}
        )

        unidad_asignada = (
            "Unidad Alfa-01 (Intervención Rápida B2G)" 
            if es_critico 
            else "Unidad Bravo-02 (Soporte Urbano)"
        )
        tiempo_despliegue = "3 a 6 minutos" if es_critico else "8 a 12 minutos"

        return AlertaResponse(
            estado="Alerta registrada y despachada con éxito en PostGIS",
            alerta_id=alerta_db.id,
            origen=origen,
            confirmacion=confirmacion,
            coordenadas={"lat": alerta_in.latitud, "lng": alerta_in.longitud},
            enrutamiento_institucional=EnrutamientoInstitucional(
                departamento="Cajamarca",
                institucion_responsable=institucion,
                prioridad=alerta_in.nivel_gravedad,
                tiempo_estimado_despliegue=tiempo_despliegue
            ),
            notificacion_familiar=NotificacionFamiliar(
                familiares_alertados=nombres_familiares,
                canal=notif_resultado["canal"]
            ),
            recurso_asignado=RecursoAsignado(
                unidad=unidad_asignada,
                estado="Desplazándose hacia coordenadas georreferenciadas"
            )
        )

    def listar_alertas_activas(self, limit: int = 50) -> List[AlertaDetalle]:
        """Extrae alertas activas con coordenadas geométricas nativas."""
        query_result = self.alert_repo.get_active_alerts_with_coords(limit=limit)
        alertas: List[AlertaDetalle] = []

        for alerta, lat, lng in query_result:
            es_critico = (alerta.nivel_gravedad or 3) >= 4
            alertas.append(AlertaDetalle(
                id=alerta.id,
                dispositivo_id=alerta.dispositivo_id,
                usuario=alerta.dispositivo_id,
                tipo_emergencia=alerta.tipo_emergencia,
                nivel_gravedad=alerta.nivel_gravedad or 3,
                origen_alerta="AUTOMATICO_INERCIA" if es_critico else "MANUAL",
                estado_confirmacion="EXPIRADO_INCONSCIENTE" if es_critico else "CONFIRMADO",
                latitud=float(lat),
                longitud=float(lng),
                timestamp_dispositivo=alerta.timestamp_dispositivo,
                creado_en=alerta.creado_en
            ))
        return alertas
