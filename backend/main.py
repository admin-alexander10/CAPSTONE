from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Asegurar que el directorio backend esté en sys.path para importaciones absolutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base

# Importar modelos para que Base.metadata los reconozca al arrancar
import app.models

# Intentar inicialización de esquema si PostgreSQL está en línea
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Nota: No se pudo conectar a la BD durante el arranque ({e}). Iniciando API...")

from app.api.middlewares import AuditLoggingMiddleware, setup_exception_handlers
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API oficial para enrutamiento de emergencia B2G, gestión de privacidad activa y detección Zero-Touch."
)

# Configuración de Middlewares (Auditoría y CORS)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejo centralizado de excepciones del dominio
setup_exception_handlers(app)

@app.get("/")
def raiz():
    return {
        "sistema": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "estado": "Operativo",
        "mensaje": "GEORESCUE IA Backend Activo",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Rutas canónicas versionadas (/api/v1/...)
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)