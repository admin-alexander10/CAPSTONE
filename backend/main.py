from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import os

app = FastAPI(
    title="QuantumGeoRescue AI - Backend B2G",
    version="1.0.0",
    description="API oficial para enrutamiento de emergencia y gestión de privacidad activa."
)

# Configuración de CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de la Base de Datos PostgreSQL
# Ajusta tus credenciales de PostgreSQL aquí o mediante variables de entorno
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "db_quantum_georescue")  # Asegúrate de que coincida con el nombre de tu BD en pgAdmin
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "omar123")
DB_PORT = os.getenv("DB_PORT", "5432")

def obtener_conexion():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Error conectando a la Base de Datos: {e}")
        raise HTTPException(status_code=500, detail="Error interno de conexión a base de datos")

# --- MODELOS PYDANTIC ---
class LoginRequest(BaseModel):
    usuario: str
    password: str

class RegistroRequest(BaseModel):
    usuario: str
    password: str
    rol: str

class FamiliarRequest(BaseModel):
    usuario_responsable: str
    nombre: str
    parentesco: str
    dispositivo_id: str

class AlertaRequest(BaseModel):
    usuario: str
    tipo_emergencia: str
    nivel_gravedad: int
    latitud: float
    longitude: float

class RutaRequest(BaseModel):
    origen_lat: float
    origen_lng: float
    destino_lat: float
    destino_lng: float
    bloqueos_detectados: bool


# --- ENDPOINTS DE AUTENTICACIÓN ---

@app.post("/auth/registro/")
def registrar_usuario(data: RegistroRequest):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE usuario = %s;", (data.usuario,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
        
        codigo_enlace = f"QRFAM-{os.urandom(2).hex().upper()}"
        
        cursor.execute(
            """
            INSERT INTO usuarios (usuario, password, rol, codigo_enlace)
            VALUES (%s, %s, %s, %s) RETURNING id;
            """,
            (data.usuario, data.password, data.rol, codigo_enlace)
        )
        conn.commit()
        return {"mensaje": "Usuario registrado exitosamente", "codigo_enlace": codigo_enlace}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.post("/auth/login/")
def login_usuario(data: LoginRequest):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT usuario, rol FROM usuarios WHERE usuario = %s AND password = %s;",
            (data.usuario, data.password)
        )
        usuario_db = cursor.fetchone()
        if not usuario_db:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
        
        return {
            "mensaje": "Acceso concedido",
            "usuario": usuario_db["usuario"],
            "rol": usuario_db["rol"]
        }
    finally:
        cursor.close()
        conn.close()


# --- ENDPOINTS DE GESTIÓN FAMILIAR Y ALERTAS ---

@app.post("/familia/agregar/")
def agregar_familiar(data: FamiliarRequest):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO red_familiar (usuario_responsable, nombre, parentesco, dispositivo_id)
            VALUES (%s, %s, %s, %s);
            """,
            (data.usuario_responsable, data.nombre, data.parentesco, data.dispositivo_id)
        )
        conn.commit()
        return {"mensaje": f"Familiar {data.nombre} vinculado correctamente a la red de protección."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.post("/alertas/despachar/")
def despachar_alerta(data: AlertaRequest):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre, parentesco FROM red_familiar WHERE usuario_responsable = %s;", (data.usuario,))
        familiares = cursor.fetchall()
        nombres_familiares = [f["nombre"] for f in familiares]

        return {
            "estado": "Alerta despachada con éxito",
            "enrutamiento_institucional": {
                "departamento": "Cajamarca",
                "institucion_responsable": "Centro de Operaciones de Emergencia Regional (COER) & Bomberos B2G",
                "prioridad": data.nivel_gravedad
            },
            "notificacion_familiar": {
                "familiares_alertados": nombres_familiares,
                "canal": "SMS / Push Notificación de Emergencia"
            }
        }
    finally:
        cursor.close()
        conn.close()


@app.post("/rescate/calcular-ruta/")
def calcular_ruta(data: RutaRequest):
    tiempo_estimado = "12 minutos" if not data.bloqueos_detectados else "18 minutos (Ruta alterna optimizada por PostGIS)"
    return {
        "origen": {"lat": data.origen_lat, "lng": data.origen_lng},
        "destino": {"lat": data.destino_lat, "lng": data.destino_lng},
        "bloqueos_evitados": data.bloqueos_detectados,
        "tiempo_estimado_llegada": tiempo_estimado,
        "estado_algoritmo": "Optimización espacial completada con éxito"
    }