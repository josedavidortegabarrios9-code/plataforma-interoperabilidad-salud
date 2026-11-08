"""
Módulo de parsing y validación de mensajes HL7 v2 y archivos CSV legados.
Valida reglas de negocio, integridad de campos y mapeo terminológico (CIE-10 / LOINC).
"""

from typing import Dict, Any, List, Tuple, Optional
import re

# Tabla de terminologías de referencia oficial (según 05_ref_terminologia.csv)
TERMINOLOGIA_CIE10 = {
    "DIARREA": ("A09", "Diarrea y gastroenteritis"),
    "HIPERTENSION": ("I10", "Hipertensión esencial"),
    "DIABETES": ("E11.9", "Diabetes mellitus tipo 2"),
    "ASMA": ("J45.9", "Asma"),
    "INFECCION URINARIA": ("N39.0", "Infección de vías urinarias"),
    "LUMBAGO": ("M54.5", "Lumbago"),
    "NEUMONIA": ("J18.9", "Neumonía"),
    "CEFALEA": ("R51", "Cefalea")
}

# Códigos CIE-10 reconocidos directamente
CIE10_VALIDOS = {"A09", "I10", "E11.9", "J45.9", "N39.0", "M54.5", "J18.9", "R51"}

class MessageValidationError(Exception):
    def __init__(self, reasons: List[str]):
        self.reasons = reasons
        super().__init__(", ".join(reasons))

class HL7Parser:
    @staticmethod
    def parse(raw_text: str) -> Dict[str, Any]:
        """
        Parsea un mensaje HL7 v2 en texto plano delimitado por salto de línea y pipes.
        Soporta mensajes con saltos de línea explícitos o compactos (MSH...PID...PV1...).
        """
        segments = {}
        # Normalizar saltos de línea (CR, LF, CRLF)
        normalized_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.strip() for line in normalized_text.split('\n') if line.strip()]

        for line in lines:
            parts = line.split("|")
            seg_name = parts[0]
            if seg_name == "MSH":
                fields = ["MSH", "|"] + parts[1:]
            else:
                fields = parts
            segments[seg_name] = fields

        return segments

    @classmethod
    def validate_and_extract_hl7(cls, raw_text: str) -> Tuple[Dict[str, Any], List[str]]:
        reasons = []
        parsed = cls.parse(raw_text)
        
        msh = parsed.get("MSH")
        pid = parsed.get("PID")
        pv1 = parsed.get("PV1")
        dg1 = parsed.get("DG1")
        obr = parsed.get("OBR")
        obx = parsed.get("OBX")

        if not msh:
            return {}, ["Mensaje no contiene segmento MSH válido"]

        sede_raw = msh[4] if len(msh) > 4 else "SEDE1"
        sede_num = 1
        if "2" in sede_raw:
            sede_num = 2
        elif "3" in sede_raw:
            sede_num = 3

        msg_type = msh[9] if len(msh) > 9 else "ADT^A01"
        msg_id = msh[10] if len(msh) > 10 else f"MSG-{hash(raw_text)}"

        # Validaciones PID
        if not pid or len(pid) <= 3:
            reasons.append("Segmento PID ausente o incompleto")
            return {}, reasons

        doc_raw = pid[3].split("^")[0] if len(pid) > 3 else ""
        if not doc_raw.isdigit():
            reasons.append("documento no numérico")

        # Nombre y apellido (PID-5: Apellido^Nombre)
        nombre_raw = pid[5] if len(pid) > 5 else "Paciente^Clinico"
        name_parts = nombre_raw.split("^")
        apellido = name_parts[0] if len(name_parts) > 0 else ""
        nombre = name_parts[1] if len(name_parts) > 1 else ""

        fecha_nac = pid[7] if len(pid) > 7 else "19900101"

        # Sexo (PID-8)
        sexo = pid[8].upper() if len(pid) > 8 else ""
        if sexo not in ("M", "F"):
            reasons.append("sexo no válido")

        # PV1
        encounter_id = "0100"
        clase = "AMB"
        medico = "Dr. Asignado"
        fecha_atencion = "20261107100000"
        if pv1:
            clase = pv1[2] if len(pv1) > 2 else "AMB"
            medico = pv1[7].replace("^", " ") if len(pv1) > 7 else "Dr. Médico"
            encounter_id = pv1[19] if len(pv1) > 19 else "0100"
            fecha_atencion = pv1[44] if len(pv1) > 44 else "20261107100000"

        # Diagnóstico (DG1)
        cod_cie10 = None
        desc_cie10 = None
        if dg1 and len(dg1) > 3:
            dg_parts = dg1[3].split("^")
            cod_dx = dg_parts[0].strip().upper()
            desc_dx = dg_parts[1].strip() if len(dg_parts) > 1 else ""
            coding_sys = dg_parts[2].strip().upper() if len(dg_parts) > 2 else ""
            
            # En HL7 ADT, si el coding system es Local ('L') o el código no es un código CIE-10 estándar (I10/ICD-10)
            if coding_sys in ("I10", "ICD10", "CIE10") and cod_dx in CIE10_VALIDOS:
                cod_cie10 = cod_dx
                desc_cie10 = desc_dx or cod_dx
            elif cod_dx in CIE10_VALIDOS and coding_sys != "L":
                cod_cie10 = cod_dx
                desc_cie10 = desc_dx or cod_dx
            else:
                reasons.append("diagnóstico sin mapeo a CIE-10")
        elif "ADT" in msg_type:
            reasons.append("diagnóstico sin mapeo a CIE-10")

        # Observación / Laboratorio (OBX)
        obs_data = None
        if obx and len(obx) > 5:
            cod_loinc = obx[3].split("^")[0] if len(obx) > 3 else "718-7"
            desc_loinc = obx[3].split("^")[1] if len(obx) > 3 and "^" in obx[3] else "Hemoglobina"
            valor = obx[5] if len(obx) > 5 else "0"
            unidad = obx[6] if len(obx) > 6 else "g/dL"
            obs_data = {
                "cod_loinc": cod_loinc,
                "desc_loinc": desc_loinc,
                "valor": float(valor.replace(",", ".")),
                "unidad": unidad
            }

        extracted = {
            "id_mensaje": msg_id,
            "sede": sede_num,
            "tipo_mensaje": msg_type,
            "documento": doc_raw,
            "nombre": nombre,
            "apellido": apellido,
            "fecha_nacimiento": fecha_nac,
            "sexo": sexo,
            "encounter_id": encounter_id,
            "clase": clase,
            "medico": medico,
            "fecha_atencion": fecha_atencion,
            "cod_cie10": cod_cie10,
            "desc_cie10": desc_cie10,
            "observacion": obs_data
        }

        return extracted, reasons

class CSVParser:
    @staticmethod
    def parse_line(line: str, line_num: int) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Parsea una línea CSV con separador ';'
        Cabecera esperada: documento;nombre;sexo;nacimiento;dx_local;fecha;triage;profesional
        """
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 8:
            return None, ["Columnas incompletas en la línea"]

        doc, nombre_comp, sexo, nacimiento, dx_local, fecha, triage, profesional = parts
        reasons = []

        # Validación documento
        if not doc.isdigit() or len(doc) <= 2:
            reasons.append("documento de 2 dígitos o no numérico")

        # Validación sexo
        sexo_clean = sexo.upper()
        if sexo_clean not in ("M", "F"):
            reasons.append("sexo no válido")

        # Validación mapeo diagnóstico
        dx_clean = dx_local.strip().upper()
        cod_cie10 = None
        desc_cie10 = None
        if dx_clean in TERMINOLOGIA_CIE10:
            cod_cie10, desc_cie10 = TERMINOLOGIA_CIE10[dx_clean]
        elif dx_clean in CIE10_VALIDOS:
            cod_cie10 = dx_clean
            desc_cie10 = dx_clean
        else:
            reasons.append("dx sin mapeo")

        # Separar nombre
        names = nombre_comp.split()
        nombre = names[0] if names else "Paciente"
        apellido = " ".join(names[1:]) if len(names) > 1 else "Sede3"

        data = {
            "documento": doc,
            "nombre": nombre,
            "apellido": apellido,
            "sexo": sexo_clean,
            "fecha_nacimiento": nacimiento,
            "cod_cie10": cod_cie10,
            "desc_cie10": desc_cie10,
            "fecha_atencion": fecha,
            "triage": triage or "3",
            "medico": profesional or "Dr. Sede 3",
            "encounter_id": f"CSV-{doc}-{line_num}"
        }

        return data, reasons
