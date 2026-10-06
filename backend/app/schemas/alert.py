from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class AlertaCreate(BaseModel):
    dispositivo_id: Optional[str] = None
    usuario: Optional[str] = None
    tipo_emergencia: str = Field(default="Sismo SOS")
    nivel_gravedad: int = Field(default=3, ge=1, le=5)
    latitud: float
    longitud: float
    timestamp_dispositivo: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def normalizar_campos(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalizar longitude -> longitud
            if "longitude" in data and "longitud" not in data:
                data["longitud"] = data["longitude"]
            # Asegurar dispositivo_id
            if "usuario" in data and not data.get("dispositivo_id"):
                data["dispositivo_id"] = data["usuario"]
            elif "dispositivo_id" in data and not data.get("usuario"):
                data["usuario"] = data["dispositivo_id"]
        return data

class EnrutamientoInstitucional(BaseModel):
    departamento: str = "Cajamarca"
    institucion_responsable: str = "Centro de Operaciones de Emergencia Regional (COER) & Bomberos B2G"
    prioridad: int
    tiempo_estimado_despliegue: str = "4 a 8 minutos"

class NotificacionFamiliar(BaseModel):
    familiares_alertados: List[str]
    canal: str = "SMS / Push Notificación de Emergencia"

class RecursoAsignado(BaseModel):
    unidad: str = "Unidad Alfa-01 (Rescate Rápido B2G)"
    estado: str = "En camino al punto de coordenadas"

class AlertaResponse(BaseModel):
    estado: str
    alerta_id: int
    origen: str = "MANUAL"
    confirmacion: str = "CONFIRMADO"
    coordenadas: Dict[str, float]
    enrutamiento_institucional: EnrutamientoInstitucional
    notificacion_familiar: NotificacionFamiliar
    recurso_asignado: RecursoAsignado

class AlertaDetalle(BaseModel):
    id: int
    dispositivo_id: str
    usuario: Optional[str] = None
    tipo_emergencia: str
    nivel_gravedad: Optional[int] = 3
    origen_alerta: Optional[str] = "MANUAL"
    estado_confirmacion: Optional[str] = "CONFIRMADO"
    latitud: float
    longitud: float
    timestamp_dispositivo: Optional[datetime] = None
    creado_en: Optional[datetime] = None
