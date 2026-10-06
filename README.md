# 🛰️ QuantumGeoRescue AI

> **Plataforma Nacional de Respuesta a Emergencias B2G & Privacidad Activa B2C**  
> Desarrollado con FastAPI, PostgreSQL + PostGIS, SQLAlchemy y Leaflet.js.

---

## 📌 Visión del Sistema

**QuantumGeoRescue AI** es una solución integral diseñada para modernizar la gestión de emergencias y operaciones de rescate ante catástrofes naturales (sismos, derrumbes e incidentes urbanos). Cuenta con un diseño dual:

1. **Portal Ciudadano (B2C)**:
   * **Privacidad Activa**: La geolocalización del usuario permanece oculta en reposo (*Modo Seguro*).
   * **Detección Inercial Zero-Touch**: Ante un sismo severo ($\ge 4$ en escala de gravedad), el sistema activa un conteo regresivo de 10 segundos. Si el usuario no responde o pierde el conocimiento, la alerta se despacha automáticamente en estado `EXPIRADO_INCONSCIENTE`.
   * **Red Familiar**: Vinculación de parientes mediante códigos únicos (`QRFAM-XXXX`) para notificación inmediata multicanal.

2. **Centro de Comando Táctico (B2G)**:
   * **Monitoreo Espacial en Tiempo Real**: Recepción de alertas con geometrías nativas PostGIS (`POINT`, SRID 4326).
   * **Enrutamiento de Rescate con Evasión de Bloqueos**: Cálculo de rutas óptimas entre la base de respuesta (COER / Bomberos) y el lugar del incidente, adaptándose dinámicamente si hay vías obstruidas o escombros.

---

## 🏗️ Arquitectura del Repositorio

```text
quantum_georescue_backend/
│
├── .gitignore                      # Exclusión formal de venv/, cache y credenciales
├── .env.example                    # Plantilla de variables de entorno
├── README.md                       # Documentación técnica completa
│
├── database/
│   └── init_db.sql                 # Script DDL (PostGIS, índices espaciales GiST, tablas)
│
├── backend/
│   ├── app/
│   │   ├── core/                   # Configuración y seguridad (hash PBKDF2, tokens)
│   │   ├── db/                     # Sesión SQLAlchemy y Base declarativa
│   │   ├── models/                 # Modelos ORM (Usuario, RedFamiliar, AlertaEmergencia)
│   │   ├── schemas/                # Validación de datos con Pydantic v2
│   │   ├── crud/                   # Consultas a base de datos y GeoAlchemy2
│   │   ├── services/               # Lógica de despacho y enrutamiento vial
│   │   └── api/v1/                 # Endpoints REST modulares
│   │
│   ├── main.py                     # Entrypoint de FastAPI, Middlewares y Swagger docs
│   ├── requirements.txt            # Dependencias de Python
│   └── venv/                       # Entorno virtual
│
└── frontend/
    ├── index.html                  # Interfaz unificada (Ciudadano B2C y Centro B2G)
    ├── css/
    │   └── styles.css              # Estilos personalizados y animaciones de radar/pulso
    └── js/
        ├── config.js               # Parámetros globales y claves
        ├── api.js                  # Cliente HTTP desacoplado
        └── app.js                  # Controlador de estados, mapa Leaflet y sismógrafo
```

---

## 🚀 Puesta en Marcha Rápida

### 1. Configuración de Base de Datos (PostgreSQL + PostGIS)
Asegúrate de tener PostgreSQL y la extensión PostGIS instalados.
Ejecuta el script de inicialización en tu gestor (pgAdmin, DBeaver o psql):

```bash
psql -U postgres -d db_quantum_georescue -f database/init_db.sql
```

### 2. Configurar Variables de Entorno
Copia el archivo de ejemplo y ajusta tus credenciales si es necesario:

```bash
cp .env.example .env
```

### 3. Iniciar el Servidor Backend (FastAPI)
Desde la carpeta `backend`, activa tu entorno virtual y arranca el servidor:

```powershell
# En Windows PowerShell:
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Acceso a la documentación interactiva Swagger:  
👉 **http://localhost:8000/docs**

### 4. Abrir la Aplicación Frontend
Puedes abrir directamente el archivo `frontend/index.html` en tu navegador, o servirlo con cualquier servidor estático:

```powershell
cd frontend
python -m http.server 3000
```
Y abre tu navegador en **http://localhost:3000**.

---

## 🛡️ Seguridad Implementada
* **Hash de contraseñas**: Algoritmo `PBKDF2-HMAC-SHA256` con sal criptográfica aleatoria de 16 bytes y 100,000 iteraciones (librería estándar, sin vulnerabilidades de texto plano).
* **Compatibilidad de migración**: Detección inteligente para cuentas de prueba previas.
* **Geolocalización segura**: Principio de menor privilegio sobre la exposición de coordenadas personales.
