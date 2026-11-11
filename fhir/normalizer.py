"""
Normalizador a HL7 FHIR R4 para Plataforma de Interoperabilidad Clínica.
Transforma datos legados (BD, HL7 v2 y CSV) a recursos estandarizados:
- Patient
- Encounter
- Condition (CIE-10)
- Observation (LOINC)
Empaquetados en un Bundle de tipo transaction con IDs deterministas y método PUT.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime

class FHIRNormalizer:
    @staticmethod
    def _format_date(date_val: Any) -> Optional[str]:
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val.strftime("%Y-%m-%d")
        d_str = str(date_val).strip()
        if len(d_str) == 8 and d_str.isdigit():  # YYYYMMDD
            return f"{d_str[0:4]}-{d_str[4:6]}-{d_str[6:8]}"
        if "T" in d_str:
            return d_str.split("T")[0]
        return d_str[:10]

    @staticmethod
    def _format_datetime(dt_val: Any) -> Optional[str]:
        if not dt_val:
            return None
        if isinstance(dt_val, datetime):
            return dt_val.strftime("%Y-%m-%dT%H:%M:%S-05:00")
        dt_str = str(dt_val).strip()
        if len(dt_str) == 14 and dt_str.isdigit():  # YYYYMMDDHHMMSS
            return f"{dt_str[0:4]}-{dt_str[4:6]}-{dt_str[6:8]}T{dt_str[8:10]}:{dt_str[10:12]}:{dt_str[12:14]}-05:00"
        if "T" in dt_str:
            if not dt_str.endswith("-05:00") and not dt_str.endswith("Z"):
                return f"{dt_str}:00-05:00" if len(dt_str) == 16 else f"{dt_str}-05:00"
            return dt_str
        return f"{dt_str}T00:00:00-05:00"

    @staticmethod
    def _map_gender(sexo: Optional[str]) -> str:
        s = str(sexo).upper() if sexo else ""
        if s in ("M", "MASCULINO", "MALE"):
            return "male"
        if s in ("F", "FEMENINO", "FEMALE"):
            return "female"
        return "other"

    @classmethod
    def build_patient(cls, doc: str, nombre: str, apellido: str, fecha_nac: Any, sexo: str, sede: str = "Central") -> Dict[str, Any]:
        patient_id = f"pac-{doc}"
        return {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [
                {
                    "system": "https://minsalud.gov.co/id/cc",
                    "value": str(doc)
                }
            ],
            "name": [
                {
                    "use": "official",
                    "family": apellido.strip() if apellido else "",
                    "given": [nombre.strip()] if nombre else []
                }
            ],
            "gender": cls._map_gender(sexo),
            "birthDate": cls._format_date(fecha_nac),
            "managingOrganization": {
                "display": f"Sede {sede}"
            }
        }

    @classmethod
    def build_encounter(cls, encounter_id: str, doc: str, fecha_ingreso: Any, clase: str = "AMB", medico: str = "Dr. Asignado", sede: str = "Central") -> Dict[str, Any]:
        patient_ref = f"Patient/pac-{doc}"
        clase_code = "AMB"
        clase_display = "Ambulatory"
        if clase.upper() in ("E", "EMER", "URGENCIAS", "URGENCIA"):
            clase_code = "EMER"
            clase_display = "Emergency"
        elif clase.upper() in ("I", "IMP", "HOSPITALIZACION"):
            clase_code = "IMP"
            clase_display = "Inpatient"

        return {
            "resourceType": "Encounter",
            "id": f"enc-{encounter_id}",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": clase_code,
                "display": clase_display
            },
            "subject": {
                "reference": patient_ref
            },
            "period": {
                "start": cls._format_datetime(fecha_ingreso)
            },
            "participant": [
                {
                    "individual": {
                        "display": medico
                    }
                }
            ],
            "serviceProvider": {
                "display": f"Sede {sede}"
            }
        }

    @classmethod
    def build_condition(cls, cond_id: str, doc: str, encounter_id: str, cod_cie10: str, desc_cie10: str, fecha: Any = None) -> Dict[str, Any]:
        return {
            "resourceType": "Condition",
            "id": f"cond-{cond_id}",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active"
                    }
                ]
            },
            "code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": cod_cie10,
                        "display": desc_cie10
                    }
                ],
                "text": desc_cie10
            },
            "subject": {
                "reference": f"Patient/pac-{doc}"
            },
            "encounter": {
                "reference": f"Encounter/enc-{encounter_id}"
            },
            "recordedDate": cls._format_date(fecha) if fecha else datetime.now().strftime("%Y-%m-%d")
        }

    @classmethod
    def build_observation(cls, obs_id: str, doc: str, encounter_id: str, cod_loinc: str, desc_loinc: str, valor: float, unidad: str) -> Dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": f"obs-{obs_id}",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": cod_loinc,
                        "display": desc_loinc
                    }
                ],
                "text": desc_loinc
            },
            "subject": {
                "reference": f"Patient/pac-{doc}"
            },
            "encounter": {
                "reference": f"Encounter/enc-{encounter_id}"
            },
            "valueQuantity": {
                "value": float(valor),
                "unit": unidad,
                "system": "http://unitsofmeasure.org",
                "code": unidad
            }
        }

    @classmethod
    def build_transaction_bundle(cls, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Empaqueta una lista de recursos FHIR en un Bundle tipo transaction con PUT determinista.
        Esto garantiza idempotencia total en HAPI FHIR sin duplicación de registros.
        """
        entries = []
        for res in resources:
            res_type = res["resourceType"]
            res_id = res["id"]
            entries.append({
                "fullUrl": f"{res_type}/{res_id}",
                "resource": res,
                "request": {
                    "method": "PUT",
                    "url": f"{res_type}/{res_id}"
                }
            })

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": entries
        }
