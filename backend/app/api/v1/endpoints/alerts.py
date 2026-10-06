from datetime import datetime

from fastapi import APIRouter, Depends, status
from typing import List
from app.schemas.alert import AlertaCreate, AlertaResponse, AlertaDetalle
from app.services.alert_service import AlertService
from app.api.deps import get_alert_service, get_current_user, require_permission
from app.services.realtime import institutional_alert_hub
from app.core.config import settings

router = APIRouter(prefix="/alertas", tags=["Alertas de Emergencia"])

@router.post("/despachar/", response_model=AlertaResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("alert:dispatch"))])
async def despachar_alerta(
    data: AlertaCreate,
    user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Controlador de despacho de alerta geoespacial.
    Persiste en PostGIS y activa el enrutamiento táctico institucional y familiar.
    """
    data.usuario = user["sub"]
    data.dispositivo_id = user["sub"]
    response = alert_service.despachar_alerta(data)
    await institutional_alert_hub.publish_alert(settings.DEFAULT_RESPONSE_INSTITUTION, {
        "type": "alert.created",
        "alert_id": response.alerta_id,
        "emergency_type": data.tipo_emergencia,
        "severity": data.nivel_gravedad,
        "latitude": data.latitud,
        "longitude": data.longitud,
        "created_at": datetime.utcnow().isoformat() + "Z",
    })
    return response

@router.get("/activas/", response_model=List[AlertaDetalle], dependencies=[Depends(require_permission("map:view"))])
def listar_alertas_activas(
    limit: int = 50,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Controlador táctico B2G para visualizar alertas georreferenciadas en tiempo real."""
    return alert_service.listar_alertas_activas(limit=limit)
