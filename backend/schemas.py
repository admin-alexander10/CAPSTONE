from pydantic import BaseModel
from datetime import datetime

class AlertaCreate(BaseModel):
    dispositivo_id: str
    tipo_emergencia: str
    nivel_gravedad: int
    latitud: float
    longitud: float
    timestamp_dispositivo: datetime

class AlertaResponse(BaseModel):
    mensaje: str
    alerta_id: int
    origen: str
    estado: str
    coordenadas: dict

    class Config:
        from_attributes = True