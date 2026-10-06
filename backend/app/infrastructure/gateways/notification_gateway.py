import logging
from typing import List, Dict, Any
from app.domain.interfaces.gateways import INotificationGateway

logger = logging.getLogger("georescue.notifications")

class EmergencyNotificationGateway(INotificationGateway):
    """
    Pasarela de notificaciones de emergencia:
    Maneja el despacho multi-canal (SMS de señalización de contingencia, Push y Canales Tácticos B2G).
    """

    def notify_family_members(
        self,
        familiares: List[str],
        tipo_emergencia: str,
        coordenadas: Dict[str, float],
        es_critico: bool
    ) -> Dict[str, Any]:
        canal = "SMS Prioritario / Señalización 2G" if es_critico else "Push Notificación Cifrada"
        logger.info(
            f"[DESPACHO NOTIFICACION] Alerta a {len(familiares)} familiares. "
            f"Tipo: {tipo_emergencia}, Canal: {canal}, Coords: {coordenadas}"
        )
        return {
            "estado": "DESPACHADO",
            "familiares_alertados": familiares,
            "canal": canal,
            "prioridad_alta": es_critico
        }

    def dispatch_institutional_alert(
        self,
        institucion: str,
        alerta_id: int,
        tipo_emergencia: str,
        prioridad: int,
        coordenadas: Dict[str, float]
    ) -> Dict[str, Any]:
        logger.warning(
            f"[DESPACHO INSTITUCIONAL B2G] Destino: {institucion}, "
            f"Alerta ID: {alerta_id}, Severidad: {prioridad}, Coords: {coordenadas}"
        )
        tiempo_estimado = "3 a 6 minutos" if prioridad >= 4 else "8 a 12 minutos"
        return {
            "institucion_responsable": institucion,
            "prioridad": prioridad,
            "tiempo_estimado_despliegue": tiempo_estimado,
            "canal_comunicacion": "Canal Táctico B2G Seguro"
        }
