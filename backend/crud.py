from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
import models
import schemas

def crear_alerta_en_db(db: Session, alerta: schemas.AlertaCreate):
    punto_wkt = f"POINT({alerta.longitud} {alerta.latitud})"
    ubicacion_geo = WKTElement(punto_wkt, srid=4326)

    # Lógica Zero-Touch: Si la gravedad es alta, se asume activación automática por inercia/sismo
    es_automatico = alerta.nivel_gravedad >= 4

    nueva_alerta = models.AlertaEmergencia(
        dispositivo_id=alerta.dispositivo_id,
        tipo_emergencia=alerta.tipo_emergencia,
        nivel_gravedad=alerta.nivel_gravedad,
        ubicacion=ubicacion_geo,
        timestamp_dispositivo=alerta.timestamp_dispositivo,
        origen_alerta="AUTOMATICO_INERCIA" if es_automatico else "MANUAL",
        estado_confirmacion="EXPIRADO_INCONSCIENTE" if es_automatico else "CONFIRMADO",
        sincronizado=True
    )

    db.add(nueva_alerta)
    db.commit()
    db.refresh(nueva_alerta)
    return nueva_alerta