from pydantic import BaseModel, Field
from typing import Dict, List, Any

class RutaRequest(BaseModel):
    origen_lat: float
    origen_lng: float
    destino_lat: float
    destino_lng: float
    bloqueos_detectados: bool = Field(default=False)

class RutaResponse(BaseModel):
    origen: Dict[str, float]
    destino: Dict[str, float]
    bloqueos_evitados: bool
    distancia_km: float
    tiempo_estimado_llegada: str
    estado_algoritmo: str
    puntos_ruta: List[List[float]] = []
