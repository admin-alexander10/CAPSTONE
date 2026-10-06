from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class RoboCoaccionCreate(BaseModel):
    dispositivo_id: Optional[str] = None
    usuario: Optional[str] = None
    tipo_amenaza: str = Field(default="coaccion")
    descripcion: str = Field(default="Amenaza de robo o coacción")
    amenaza_detectada: bool = False
    activar_panic_silencioso: bool = False
    nivel_gravedad: int = Field(default=5, ge=1, le=5)
    latitud: float
    longitud: float
    timestamp_dispositivo: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def normalizar_campos(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "longitude" in data and "longitud" not in data:
                data["longitud"] = data["longitude"]
            if "usuario" in data and not data.get("dispositivo_id"):
                data["dispositivo_id"] = data["usuario"]
            elif "dispositivo_id" in data and not data.get("usuario"):
                data["usuario"] = data["dispositivo_id"]
        return data


class RoboCoaccionResponse(BaseModel):
    estado: str
    alerta_id: int
    tipo_emergencia: str = "ROBO_ASALTO_COACCION"
    institucion_prioritaria: str = "Policía Nacional del Perú (PNP)"
    prioridad: int = 5
    alerta_silenciosa: bool = True
    coordenadas: Dict[str, float]
    enrutamiento_institucional: Dict[str, Any]
    notificacion_familiar: Dict[str, Any]
    recurso_asignado: Dict[str, str]
