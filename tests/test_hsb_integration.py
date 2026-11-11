"""
Pruebas de Integración de Extremo a Extremo para el HSB y Middleware Clínico.
Valida todas las condiciones exigidas por la rúbrica y por LEEME.md.
"""

import unittest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hsb.main import app, processed_messages, audit_ledger, performance_metrics

client = TestClient(app)

class TestHSBIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["TEST_MODE"] = "true"
        cls.fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    def test_01_ingesta_hl7_valido_sede2(self):
        filepath = os.path.join(self.fixtures_dir, "01_adt_a01_valido_sede2.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        res = client.post("/hsb/hl7", content=content, headers={"Content-Type": "text/plain", "X-Rol": "medico", "X-API-Key": "hsb_clinical_ingest_key_2026"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["estado"], "entregado")
        self.assertEqual(data["documento"], "1007")
        self.assertEqual(data["sede"], 2)

    def test_02_idempotencia_reenvio_duplicado(self):
        # Reenviar el mismo mensaje exactamente debe devolver duplicado y no volver a crearlo
        filepath = os.path.join(self.fixtures_dir, "01_adt_a01_valido_sede2.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        res = client.post("/hsb/hl7", content=content, headers={"Content-Type": "text/plain", "X-Rol": "medico", "X-API-Key": "hsb_clinical_ingest_key_2026"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["estado"], "duplicado")
        self.assertIn("ya fue procesado previamente", data["mensaje"])

    def test_03_ingesta_hl7_laboratorio_sede1(self):
        filepath = os.path.join(self.fixtures_dir, "02_oru_r01_laboratorio_sede1.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        res = client.post("/hsb/hl7", content=content, headers={"Content-Type": "text/plain", "X-Rol": "medico", "X-API-Key": "hsb_clinical_ingest_key_2026"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["estado"], "entregado")
        self.assertEqual(data["documento"], "1001")
        self.assertEqual(data["sede"], 1)

    def test_04_ingesta_hl7_invalido_3_motivos(self):
        filepath = os.path.join(self.fixtures_dir, "03_adt_a01_invalido.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        res = client.post("/hsb/hl7", content=content, headers={"Content-Type": "text/plain", "X-Rol": "medico", "X-API-Key": "hsb_clinical_ingest_key_2026"})
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertEqual(data["estado"], "rechazado")
        motivos = data["motivos"]
        self.assertIn("documento no numérico", motivos)
        self.assertIn("sexo no válido", motivos)
        self.assertIn("diagnóstico sin mapeo a CIE-10", motivos)

    def test_05_ingesta_csv_sede3(self):
        filepath = os.path.join(self.fixtures_dir, "04_sede3_legado.csv")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        res = client.post("/hsb/csv?sede=3", content=content, headers={"Content-Type": "text/plain", "X-Rol": "medico", "X-API-Key": "hsb_clinical_ingest_key_2026"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["entregados"], 3)
        self.assertEqual(data["rechazados"], 2)

    def test_06_consulta_unificada_multisede(self):
        res = client.get("/paciente/1001/historia-unificada", headers={"X-Rol": "medico"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["paciente"]["documento"], "1001")
        # El paciente 1001 tiene registros en las 3 sedes
        sedes_presentes = {a["sede"] for a in data["atenciones"]}
        self.assertIn(1, sedes_presentes)
        self.assertIn(2, sedes_presentes)
        self.assertIn(3, sedes_presentes)

    def test_07_rbac_control_acceso(self):
        # Admisionista no puede ver historias clínicas detalladas (diagnósticos)
        res = client.get("/paciente/1001/historia-unificada", headers={"X-Rol": "admisionista"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("Acceso denegado", res.json()["detail"])

    def test_08_auditoria_cadena_hash_y_tamper_detection(self):
        # 1. Verificar que la cadena está íntegra
        res_verif = client.get("/audit/verify")
        self.assertEqual(res_verif.status_code, 200)
        self.assertTrue(res_verif.json()["integro"])

        # 2. Simular alteración maliciosa en el evento 1
        res_tamper = client.post("/audit/tamper?evento_id=1")
        self.assertEqual(res_tamper.status_code, 200)

        # 3. Verificar que el detector atrapa la alteración
        res_check = client.get("/audit/verify")
        self.assertFalse(res_check.json()["integro"])
        self.assertEqual(res_check.json()["evento_alterado_id"], 1)

    def test_09_resiliencia_caida_sede(self):
        # Simular caída de Sede 2
        client.post("/test/toggle-sede?sede_id=2")
        res = client.get("/paciente/1001/historia-unificada", headers={"X-Rol": "medico"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["degradacion_tolerante"])
        # La sede 2 debe reportarse como inactiva
        inactivas = [s["nombre"] for s in data["sedes_inactivas"]]
        self.assertIn("Cartagena", inactivas)
        # Restaurar Sede 2
        client.post("/test/toggle-sede?sede_id=2")

    def test_10_exportacion_bundle_fhir(self):
        res = client.get("/paciente/1001/bundle")
        self.assertEqual(res.status_code, 200)
        bundle = res.json()
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "transaction")
        self.assertGreater(len(bundle["entry"]), 0)

if __name__ == "__main__":
    unittest.main()
