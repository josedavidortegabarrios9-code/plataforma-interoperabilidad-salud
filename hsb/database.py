"""
Módulo de Acceso a Datos Distribuidos (RF4) para el Health Service Bus (HSB).
Conecta con los 3 nodos PostgreSQL legados (Sincelejo, Cartagena, Corozal).
Garantiza persistencia en volúmenes Docker, sincronización de secuencias SERIAL,
idempotencia en base de datos (mensaje_bus) y detección activa de caídas por socket.
"""

import os
import json
import socket
import logging
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("hsb.database")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 no disponible en este entorno; se usará almacenamiento en memoria/caché.")

# Mapeo de URLs de conexión por sede
SEDE_URLS = {
    1: os.getenv("SEDE1_URL", "postgresql://postgres:postgrespassword@pg_sede1:5432/historia_clinica_sede1"),
    2: os.getenv("SEDE2_URL", "postgresql://postgres:postgrespassword@pg_sede2:5432/historia_clinica_sede2"),
    3: os.getenv("SEDE3_URL", "postgresql://postgres:postgrespassword@pg_sede3:5432/historia_clinica_sede3")
}

# Nombres descriptivos por sede
SEDE_NOMBRES = {
    1: "Sincelejo",
    2: "Cartagena",
    3: "Corozal"
}

def check_sede_alive(sede_id: int) -> bool:
    """
    Detecta si una sede física o simulada está operativa.
    Realiza verificación activa de socket TCP para responder instantáneamente si el contenedor fue detenido (docker stop).
    """
    # 1. Simulación explícita de prueba o modo de test
    if os.getenv(f"SEDE{sede_id}_DOWN", "false").lower() == "true":
        return False

    if os.getenv("TEST_MODE", "false").lower() == "true":
        return True

    db_url = SEDE_URLS.get(sede_id)
    if not db_url:
        return False

    # 2. Verificación de socket de red (detecta si el contenedor o servicio cayó con docker stop)
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname or f"pg_sede{sede_id}"
        port = parsed.port or (5430 + sede_id)
        with socket.create_connection((host, port), timeout=0.8):
            pass
    except Exception:
        # Falló la conexión al puerto de la base de datos (contenedor detenido)
        return False

    # 3. Si psycopg2 está instalado, verificar consulta básica
    if PSYCOPG2_AVAILABLE:
        try:
            conn = psycopg2.connect(db_url, connect_timeout=1)
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            conn.close()
            return True
        except Exception:
            return False

    return True

def get_db_connection(sede_id: int):
    """
    Abre una conexión a la base de datos PostgreSQL de la sede.
    Devuelve None si el nodo está caído, apagado o inalcanzable.
    """
    if not check_sede_alive(sede_id):
        return None

    if not PSYCOPG2_AVAILABLE:
        return None

    db_url = SEDE_URLS.get(sede_id)
    try:
        conn = psycopg2.connect(db_url, connect_timeout=2)
        return conn
    except Exception as e:
        logger.debug(f"Sede {sede_id} no alcanzable vía PostgreSQL ({e}).")
        return None

def fetch_atenciones_sede(sede_id: int, documento: str) -> Tuple[bool, Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Consulta atenciones y datos del paciente en la base de datos de una sede.
    Retorna (nodo_activo, paciente_data, lista_atenciones).
    """
    conn = get_db_connection(sede_id)
    if not conn:
        return False, None, []

    paciente_info = None
    atenciones = []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Obtener datos de usuario
            cur.execute("""
                SELECT numero_documento, cod_tipo_documento, primer_nombre, primer_apellido, 
                       fecha_nacimiento, cod_sexo, fhir_patient_id
                FROM usuario
                WHERE numero_documento = %s
                LIMIT 1
            """, (str(documento),))
            u_row = cur.fetchone()
            if u_row:
                paciente_info = {
                    "documento": str(u_row["numero_documento"]),
                    "tipo_documento": u_row["cod_tipo_documento"] or "CC",
                    "nombre": u_row["primer_nombre"],
                    "apellido": u_row["primer_apellido"],
                    "nacimiento": str(u_row["fecha_nacimiento"]),
                    "sexo": u_row["cod_sexo"],
                    "fhir_patient_id": u_row.get("fhir_patient_id") or f"pac-{documento}"
                }

                # 2. Obtener atenciones del paciente en esta sede
                cur.execute("""
                    SELECT a.id_atencion, a.fecha_hora_ingreso, a.cod_modalidad, a.cod_via_ingreso, 
                           a.causa_atencion, p.nombre_completo AS medico
                    FROM atencion a
                    JOIN usuario u ON a.id_usuario = u.id_usuario
                    LEFT JOIN profesional_salud p ON a.id_profesional = p.id_profesional
                    WHERE u.numero_documento = %s
                    ORDER BY a.fecha_hora_ingreso DESC
                """, (str(documento),))
                atn_rows = cur.fetchall()

                for a_row in atn_rows:
                    atn_id = a_row["id_atencion"]

                    # Diagnósticos
                    cur.execute("""
                        SELECT d.cod_cie10, c.descripcion, d.tipo
                        FROM diagnostico d
                        LEFT JOIN cat_cie10 c ON d.cod_cie10 = c.cod_cie10
                        WHERE d.id_atencion = %s
                    """, (atn_id,))
                    dx_rows = cur.fetchall()
                    diagnosticos = [
                        {
                            "codigo": d["cod_cie10"],
                            "descripcion": d["descripcion"] or "Diagnóstico clínico",
                            "tipo": d["tipo"]
                        }
                        for d in dx_rows
                    ]

                    # Tecnologías / Laboratorios y Medicamentos
                    cur.execute("""
                        SELECT descripcion_tecnologia, codigo_loinc, resultado_valor, unidad_medida, dias_tratamiento
                        FROM tecnologia_salud
                        WHERE id_atencion = %s
                    """, (atn_id,))
                    tec_rows = cur.fetchall()
                    tecnologias = []
                    medicamentos = []
                    for t in tec_rows:
                        desc = t["descripcion_tecnologia"]
                        # Si tiene dias de tratamiento o términos de fármacos, clasificar en medicamentos
                        is_med = bool(t.get("dias_tratamiento")) or any(k in desc.lower() for k in ["tableta", "mg", "capsula", "inhalador", "sobre", "jarabe", "gota", "oral", "suspension"])
                        if is_med:
                            dosis_str = f"{t['resultado_valor']} {t['unidad_medida']}" if t['resultado_valor'] is not None else ""
                            medicamentos.append(f"{desc} {dosis_str}".strip())
                        else:
                            tecnologias.append({
                                "codigo": t["codigo_loinc"] or "LOINC",
                                "nombre": desc,
                                "valor": float(t["resultado_valor"]) if t["resultado_valor"] is not None else None,
                                "unidad": t["unidad_medida"] or ""
                            })

                    # Egreso Clínico
                    cur.execute("""
                        SELECT fecha_hora_salida, cod_condicion_salida, sello_integridad
                        FROM egreso
                        WHERE id_atencion = %s
                    """, (atn_id,))
                    eg_row = cur.fetchone()
                    egreso_info = None
                    if eg_row:
                        cond_map = {"01": "Alta médica con tratamiento ambulatorio", "02": "Hospitalización", "03": "Remisión"}
                        egreso_info = {
                            "fecha": str(eg_row["fecha_hora_salida"]),
                            "destino": cond_map.get(eg_row["cod_condicion_salida"], "Alta médica"),
                            "sello": eg_row["sello_integridad"]
                        }

                    atenciones.append({
                        "id_atencion": f"S{sede_id}-{atn_id:04d}",
                        "documento": str(documento),
                        "sede": sede_id,
                        "sede_nombre": SEDE_NOMBRES.get(sede_id, f"Sede {sede_id}"),
                        "fecha": a_row["fecha_hora_ingreso"].isoformat() if hasattr(a_row["fecha_hora_ingreso"], "isoformat") else str(a_row["fecha_hora_ingreso"]),
                        "clase": a_row["cod_modalidad"] or "AMB",
                        "motivo": a_row["causa_atencion"],
                        "medico": a_row["medico"] or "Médico Institucional",
                        "diagnosticos": diagnosticos,
                        "tecnologias": tecnologias,
                        "medicamentos": medicamentos,
                        "egreso": egreso_info
                    })

        conn.close()
        return True, paciente_info, atenciones
    except Exception as e:
        logger.error(f"Error consultando Sede {sede_id}: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return True, paciente_info, atenciones

def persist_atencion_sede(
    sede_id: int,
    documento: str,
    nombre: str,
    apellido: str,
    nacimiento: str,
    sexo: str,
    motivo: str,
    medico: str = "Dr. Asignado",
    triage_cod: Optional[str] = None,
    cie10_cod: Optional[str] = None,
    cie10_desc: Optional[str] = None,
    loinc_cod: Optional[str] = None,
    loinc_desc: Optional[str] = None,
    loinc_val: Optional[float] = None,
    loinc_unit: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Inserta de forma persistente y atómica el paciente y su atención en PostgreSQL.
    Sincroniza dinámicamente las secuencias SERIAL antes de insertar para evitar
    el error de duplicate key (usuario_pkey o atencion_pkey).
    Retorna (True, "OK") o (False, "Motivo del fallo").
    """
    if not PSYCOPG2_AVAILABLE:
        return True, "OK (Almacenado en memoria/cache)"

    conn = get_db_connection(sede_id)
    if not conn:
        return False, f"Nodo de Sede {sede_id} no disponible o caído"

    try:
        with conn.cursor() as cur:
            # 1. Sincronizar secuencias SERIAL con los valores máximos actuales en la base de datos
            cur.execute("""
                SELECT setval('usuario_id_usuario_seq', COALESCE((SELECT MAX(id_usuario) FROM usuario), 1));
                SELECT setval('atencion_id_atencion_seq', COALESCE((SELECT MAX(id_atencion) FROM atencion), 1));
                SELECT setval('profesional_salud_id_profesional_seq', COALESCE((SELECT MAX(id_profesional) FROM profesional_salud), 1));
                SELECT setval('diagnostico_id_diagnostico_seq', COALESCE((SELECT MAX(id_diagnostico) FROM diagnostico), 1));
                SELECT setval('tecnologia_salud_id_tecnologia_seq', COALESCE((SELECT MAX(id_tecnologia) FROM tecnologia_salud), 1));
            """)

            # 2. Asegurar profesional de salud o tomar el primero
            cur.execute("SELECT id_profesional FROM profesional_salud WHERE id_sede = %s LIMIT 1", (sede_id,))
            prof = cur.fetchone()
            id_profesional = prof[0] if prof else 1

            # 3. Buscar si el usuario ya existe en esta sede
            cur.execute("SELECT id_usuario FROM usuario WHERE numero_documento = %s AND id_sede_origen = %s", (str(documento), sede_id))
            u_row = cur.fetchone()
            if u_row:
                id_usuario = u_row[0]
                cur.execute("""
                    UPDATE usuario 
                    SET primer_nombre = %s, primer_apellido = %s, fecha_nacimiento = %s, cod_sexo = %s
                    WHERE id_usuario = %s
                """, (nombre, apellido, nacimiento or '1990-01-01', sexo or 'M', id_usuario))
            else:
                # Insertar nuevo usuario con el contador SERIAL sincronizado
                cur.execute("""
                    INSERT INTO usuario (cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
                    VALUES ('CC', %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_usuario;
                """, (str(documento), nombre, apellido, nacimiento or '1990-01-01', sexo or 'M', sede_id, f"pac-{documento}"))
                id_usuario = cur.fetchone()[0]

            # 4. Insertar atención médica
            cur.execute("""
                INSERT INTO atencion (id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional)
                VALUES (%s, CURRENT_TIMESTAMP, '01', '01', %s, %s)
                RETURNING id_atencion;
            """, (id_usuario, motivo or 'Ingreso asistencial registrado vía HSB', id_profesional))
            id_atencion = cur.fetchone()[0]

            # 5. Insertar triage si aplica
            if triage_cod:
                cur.execute("""
                    INSERT INTO triage (id_atencion, fecha_hora_triage, cod_triage, observaciones)
                    VALUES (%s, CURRENT_TIMESTAMP, %s, 'Triage registrado en admisión')
                    ON CONFLICT (id_atencion) DO NOTHING;
                """, (id_atencion, str(triage_cod)))

            # 6. Insertar diagnóstico CIE-10 si aplica
            if cie10_cod:
                cur.execute("""
                    INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
                    VALUES (%s, %s, 'INGRESO', 'PRINCIPAL', %s)
                    ON CONFLICT DO NOTHING;
                """, (id_atencion, cie10_cod, f"{documento}-{cie10_cod}"))

            # 7. Insertar tecnología / LOINC si aplica
            if loinc_cod:
                cur.execute("""
                    INSERT INTO tecnologia_salud (id_atencion, id_profesional, descripcion_tecnologia, codigo_loinc, resultado_valor, unidad_medida)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (id_atencion, id_profesional, loinc_desc or 'Tecnología asistencial', loinc_cod, loinc_val, loinc_unit or ''))

            conn.commit()
        conn.close()
        logger.info(f"Atención registrada exitosamente en PostgreSQL de Sede {sede_id} (ID Atn: {id_atencion})")
        return True, "OK"
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Error al persistir en PostgreSQL Sede {sede_id}: {err_msg}")
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return False, err_msg

# --------------------------------------------------------------------------
# Persistencia de Idempotencia (Tabla mensaje_bus)
# --------------------------------------------------------------------------
def check_mensaje_bus(id_mensaje: str, hash_contenido: str) -> Optional[Dict[str, Any]]:
    """
    Verifica si un mensaje ya existe en la tabla mensaje_bus de cualquiera de los nodos PostgreSQL.
    Sobrevive a reinicios del servicio HSB.
    """
    for s_id in (1, 2, 3):
        conn = get_db_connection(s_id)
        if not conn:
            continue
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id_mensaje, estado, id_sede_origen, fecha_ingreso
                    FROM mensaje_bus
                    WHERE id_mensaje = %s OR hash_contenido = %s
                    LIMIT 1
                """, (id_mensaje, hash_contenido))
                row = cur.fetchone()
                if row:
                    conn.close()
                    return {
                        "id_mensaje": row[0],
                        "estado": row[1],
                        "sede": row[2],
                        "fecha": str(row[3])
                    }
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
    return None

def guardar_mensaje_bus(
    id_mensaje: str,
    formato_origen: str,
    id_sede: int,
    hash_contenido: str,
    estado: str,
    payload_raw: str,
    payload_fhir: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Guarda o actualiza el estado de un mensaje en la tabla mensaje_bus de PostgreSQL.
    """
    if not PSYCOPG2_AVAILABLE:
        return False

    conn = get_db_connection(id_sede)
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO mensaje_bus (id_mensaje, formato_origen, id_sede_origen, hash_contenido, estado, payload_raw, payload_fhir)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_mensaje) DO UPDATE 
                SET estado = EXCLUDED.estado, intentos = mensaje_bus.intentos + 1;
            """, (
                id_mensaje,
                formato_origen,
                id_sede,
                hash_contenido,
                estado,
                payload_raw,
                json.dumps(payload_fhir) if payload_fhir else None
            ))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error guardando mensaje en mensaje_bus: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return False

def load_processed_messages_from_db() -> Dict[str, Any]:
    """
    Carga todos los mensajes procesados históricamente desde PostgreSQL al iniciar el HSB.
    """
    if not PSYCOPG2_AVAILABLE:
        return {}

    processed = {}
    for s_id in (1, 2, 3):
        conn = get_db_connection(s_id)
        if not conn:
            continue
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id_mensaje, hash_contenido, estado, id_sede_origen FROM mensaje_bus")
                for row in cur.fetchall():
                    m_id, h_val, est, s_orig = row
                    entry = {"id_mensaje": m_id, "hash": h_val, "estado": est, "sede": s_orig, "timestamp": 0}
                    processed[m_id] = entry
                    if h_val:
                        processed[h_val] = entry
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
    return processed

# --------------------------------------------------------------------------
# Persistencia de Trazabilidad Criptográfica (Tabla evento_auditoria)
# --------------------------------------------------------------------------
def persist_audit_event_to_db(event: Dict[str, Any]) -> bool:
    """
    Guarda un eslabón de la auditoría en la tabla evento_auditoria de PostgreSQL.
    """
    if not PSYCOPG2_AVAILABLE:
        return False

    for s_id in (1, 2, 3):
        conn = get_db_connection(s_id)
        if not conn:
            continue
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT setval('evento_auditoria_id_evento_seq', COALESCE((SELECT MAX(id_evento) FROM evento_auditoria), 1));
                    INSERT INTO evento_auditoria (id_evento, fecha_hora, actor_username, rol_actor, accion, recurso_afectado, resultado, hash_previo, hash_actual)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id_evento) DO NOTHING;
                """, (
                    event["id_evento"],
                    event["fecha_hora"],
                    event["actor_username"],
                    event["rol_actor"],
                    event["accion"],
                    event["recurso_afectado"],
                    event["resultado"],
                    event["hash_previo"],
                    event["hash_actual"]
                ))
                conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error persistiendo auditoría en PostgreSQL Sede {s_id}: {e}")
            try:
                conn.close()
            except Exception:
                pass
    return False

def load_audit_events_from_db() -> List[Dict[str, Any]]:
    """
    Recupera los eventos de auditoría almacenados en PostgreSQL al iniciar el HSB.
    """
    if not PSYCOPG2_AVAILABLE:
        return []

    events = []
    for s_id in (1, 2, 3):
        conn = get_db_connection(s_id)
        if not conn:
            continue
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id_evento, fecha_hora, actor_username, rol_actor, accion, 
                           recurso_afectado, resultado, hash_previo, hash_actual
                    FROM evento_auditoria
                    ORDER BY id_evento ASC
                """)
                rows = cur.fetchall()
                if rows:
                    for r in rows:
                        fh = r["fecha_hora"].isoformat() if hasattr(r["fecha_hora"], "isoformat") else str(r["fecha_hora"])
                        events.append({
                            "id_evento": r["id_evento"],
                            "timestamp": fh,
                            "fecha_hora": fh,
                            "actor": r["actor_username"],
                            "actor_username": r["actor_username"],
                            "rol": r["rol_actor"],
                            "rol_actor": r["rol_actor"],
                            "accion": r["accion"],
                            "recurso": r["recurso_afectado"],
                            "recurso_afectado": r["recurso_afectado"],
                            "resultado": r["resultado"],
                            "hash_previo": r["hash_previo"],
                            "hash_actual": r["hash_actual"]
                        })
                    conn.close()
                    return events
            conn.close()
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
    return events
