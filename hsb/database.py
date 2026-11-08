"""
Módulo de Acceso a Datos Distribuidos (RF4) para el Health Service Bus (HSB).
Conecta con los 3 nodos PostgreSQL legados (Sincelejo, Cartagena, Corozal).
Garantiza persistencia en volúmenes Docker y tolerancia a fallos por nodo.
"""

import os
import logging
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

def get_db_connection(sede_id: int):
    """
    Intenta abrir una conexión a la base de datos PostgreSQL de la sede indicada.
    Si la sede está caída o simulada como inactiva, devuelve None de inmediato.
    """
    # Verificación de simulación de caída para pruebas de resiliencia
    if os.getenv(f"SEDE{sede_id}_DOWN", "false").lower() == "true":
        return None

    if not PSYCOPG2_AVAILABLE:
        return None

    db_url = SEDE_URLS.get(sede_id)
    if not db_url:
        return None

    try:
        conn = psycopg2.connect(db_url, connect_timeout=2)
        return conn
    except Exception as e:
        logger.debug(f"Sede {sede_id} no alcanzable vía PostgreSQL ({e}); conmutando a tolerancia de fallos.")
        return None

def fetch_atenciones_sede(sede_id: int, documento: str) -> Tuple[bool, Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Consulta las atenciones y datos del paciente en la base de datos de una sede.
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

                    # Tecnologías / Laboratorios
                    cur.execute("""
                        SELECT descripcion_tecnologia, codigo_loinc, resultado_valor, unidad_medida
                        FROM tecnologia_salud
                        WHERE id_atencion = %s
                    """, (atn_id,))
                    tec_rows = cur.fetchall()
                    tecnologias = [
                        {
                            "codigo": t["codigo_loinc"] or "LOINC",
                            "nombre": t["descripcion_tecnologia"],
                            "valor": float(t["resultado_valor"]) if t["resultado_valor"] is not None else None,
                            "unidad": t["unidad_medida"] or ""
                        }
                        for t in tec_rows
                    ]

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
                        "tecnologias": tecnologias
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
) -> bool:
    """
    Inserta de forma persistente el paciente y su atención en el PostgreSQL de la sede destino.
    """
    conn = get_db_connection(sede_id)
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # 1. Asegurar profesional de salud o tomar el primero
            cur.execute("SELECT id_profesional FROM profesional_salud WHERE id_sede = %s LIMIT 1", (sede_id,))
            prof = cur.fetchone()
            id_profesional = prof[0] if prof else 1

            # 2. Insertar o actualizar usuario
            cur.execute("""
                INSERT INTO usuario (cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
                VALUES ('CC', %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (numero_documento, id_sede_origen) 
                DO UPDATE SET primer_nombre = EXCLUDED.primer_nombre, primer_apellido = EXCLUDED.primer_apellido
                RETURNING id_usuario;
            """, (str(documento), nombre, apellido, nacimiento or '1990-01-01', sexo or 'M', sede_id, f"pac-{documento}"))
            user_row = cur.fetchone()
            id_usuario = user_row[0]

            # 3. Insertar atención médica
            cur.execute("""
                INSERT INTO atencion (id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional)
                VALUES (%s, CURRENT_TIMESTAMP, '01', '01', %s, %s)
                RETURNING id_atencion;
            """, (id_usuario, motivo or 'Ingreso asistencial registrado vía HSB', id_profesional))
            atn_row = cur.fetchone()
            id_atencion = atn_row[0]

            # 4. Insertar triage si aplica
            if triage_cod:
                cur.execute("""
                    INSERT INTO triage (id_atencion, fecha_hora_triage, cod_triage, observaciones)
                    VALUES (%s, CURRENT_TIMESTAMP, %s, 'Triage registrado en admisión')
                    ON CONFLICT (id_atencion) DO NOTHING;
                """, (id_atencion, str(triage_cod)))

            # 5. Insertar diagnóstico CIE-10 si aplica
            if cie10_cod:
                cur.execute("""
                    INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
                    VALUES (%s, %s, 'INGRESO', 'PRINCIPAL', %s)
                    ON CONFLICT DO NOTHING;
                """, (id_atencion, cie10_cod, f"{documento}-{cie10_cod}"))

            # 6. Insertar tecnología / LOINC si aplica
            if loinc_cod:
                cur.execute("""
                    INSERT INTO tecnologia_salud (id_atencion, id_profesional, descripcion_tecnologia, codigo_loinc, resultado_valor, unidad_medida)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (id_atencion, id_profesional, loinc_desc or 'Tecnología asistencial', loinc_cod, loinc_val, loinc_unit or ''))

            conn.commit()
        conn.close()
        logger.info(f"Atención registrada exitosamente en PostgreSQL de Sede {sede_id} (ID Atn: {id_atencion})")
        return True
    except Exception as e:
        logger.error(f"Error al persistir en PostgreSQL Sede {sede_id}: {e}")
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return False
