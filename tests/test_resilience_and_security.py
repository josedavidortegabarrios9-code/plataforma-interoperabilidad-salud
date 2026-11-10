"""
Pruebas de Resiliencia Store-and-Forward, Reintentos DLQ y Seguridad 2FA Estricta.
"""
import unittest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hsb.main import app, sede_retry_queue, dead_letter_queue, processed_messages

client = TestClient(app)

class TestResilienceAndSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["TEST_MODE"] = "true"

    def test_01_sede_caida_store_and_forward(self):
        # Simular caída de Sede 1
        client.post("/test/toggle-sede?sede_id=1")
        
        # Enviar mensaje HL7 dirigido a Sede 1
        hl7_msg = (
            "MSH|^~\\&|LAB_SIS|SEDE1|HSB|CLINICA|20261108103000||ORU^R01|MSG-SF-001|P|2.5\r"
            "PID|1||1099^^^CC||Perez^Juan||19850101|M\r"
            "PV1|1|AMB|S1-0999^^^SEDE1||||MED001^Dr. Gomez\r"
            "OBX|1|NM|718-7^Hemoglobina||14.5|g/dL|12.0-16.0|N|||F"
        )
        res = client.post("/hsb/hl7", content=hl7_msg, headers={"Content-Type": "text/plain", "X-Rol": "sistema"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["estado"], "reintentando")
        self.assertTrue(data["reintentando"])
        self.assertIn("Store-and-Forward", data["motivo"])
        self.assertGreaterEqual(len(sede_retry_queue[1]), 1)

        # Restaurar Sede 1 -> debe vaciar la cola de Store-and-Forward
        res_toggle = client.post("/test/toggle-sede?sede_id=1")
        self.assertEqual(res_toggle.status_code, 200)
        self.assertEqual(len(sede_retry_queue[1]), 0)

    def test_02_2fa_seguridad_estricta_sin_backdoors(self):
        # Paso 1: Login con contraseña correcta
        res_login = client.post("/auth/login", json={"username": "medico_ruiz", "password": "medico123"})
        self.assertEqual(res_login.status_code, 200)
        data_login = res_login.json()
        self.assertEqual(data_login["status"], "pending_2fa")
        # Verificar que NO se filtre el código en el JSON de respuesta
        self.assertNotIn("codigo_demo", data_login)

        # Paso 2: Intentar backdoor anterior 807286 -> debe ser RECHAZADO (401)
        res_backdoor = client.post("/auth/verify-2fa", json={"username": "medico_ruiz", "code": "807286"})
        self.assertEqual(res_backdoor.status_code, 401)

        # Paso 3: Consultar código auténtico desde el buzón simulado
        res_mail = client.get("/auth/mailbox/medico_ruiz")
        self.assertEqual(res_mail.status_code, 200)
        data_mail = res_mail.json()
        self.assertGreater(len(data_mail["mensajes"]), 0)
        real_code = data_mail["mensajes"][0]["codigo_2fa"]
        self.assertTrue(real_code.isdigit())
        self.assertEqual(len(real_code), 6)

        # Paso 4: Validar con el código auténtico -> debe entregar Token JWT (200)
        res_verif = client.post("/auth/verify-2fa", json={"username": "medico_ruiz", "code": real_code})
        self.assertEqual(res_verif.status_code, 200)
        data_token = res_verif.json()
        token = data_token.get("token") or data_token.get("access_token")
        self.assertIsNotNone(token)
        self.assertEqual(data_token["rol"], "medico")

    def test_03_endpoint_metricas_sin_formulas_inventadas(self):
        res = client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        metrics = res.json()
        self.assertIn("total_mensajes_recibidos", metrics)
        self.assertIn("mensajes_por_minuto", metrics)
        self.assertIn("latencia_media_ms", metrics)
        self.assertIn("tasa_fallidos_porcentaje", metrics)

    def test_04_dlq_retry_endpoint(self):
        res = client.post("/hsb/dlq/retry")
        self.assertEqual(res.status_code, 200)
        self.assertIn("mensajes_reprocesados", res.json())

if __name__ == "__main__":
    unittest.main()
