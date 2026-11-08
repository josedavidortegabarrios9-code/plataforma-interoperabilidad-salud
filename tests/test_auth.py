"""
Pruebas Unitarias de Autenticación, Hashing SHA-256, JWT y RBAC (Fase 4).
"""
import unittest
from fastapi import HTTPException
from hsb.auth import hash_password, verify_password, JWTManager, require_role, USUARIOS_PRUEBA

class TestAuthSecurity(unittest.TestCase):

    def test_01_hash_password_sha256(self):
        pw = "medico123"
        h = hash_password(pw)
        self.assertEqual(len(h), 64)
        self.assertEqual(h, USUARIOS_PRUEBA["medico_ruiz"]["password_hash"])

    def test_02_verify_password_valido_e_invalido(self):
        stored_hash = USUARIOS_PRUEBA["medico_ruiz"]["password_hash"]
        self.assertTrue(verify_password("medico123", stored_hash))
        self.assertFalse(verify_password("password_falso", stored_hash))
        self.assertFalse(verify_password("", stored_hash))

    def test_03_jwt_creacion_y_validacion(self):
        token = JWTManager.create_token("medico_ruiz", "medico", "502002")
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

        payload = JWTManager.verify_token(token)
        self.assertEqual(payload["sub"], "medico_ruiz")
        self.assertEqual(payload["rol"], "medico")
        self.assertEqual(payload["doc"], "502002")

    def test_04_jwt_firma_invalida_rechazo(self):
        token = JWTManager.create_token("medico_ruiz", "medico", "502002")
        partes = token.split(".")
        # Manipular payload
        token_manipulado = f"{partes[0]}.eyJzdWIiOiAiaGFja2VyIn0.{partes[2]}"
        with self.assertRaises(HTTPException) as ctx:
            JWTManager.verify_token(token_manipulado)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_05_rbac_require_role_permitido(self):
        token = JWTManager.create_token("medico_ruiz", "medico", "502002")
        auth_header = f"Bearer {token}"
        info = require_role(allowed_roles=["medico", "auditor"], authorization=auth_header)
        self.assertEqual(info["rol"], "medico")

    def test_06_rbac_require_role_denegado_403(self):
        # Admisionista intentando entrar a ruta de médicos
        token = JWTManager.create_token("admision_sincelejo", "admisionista", "601001")
        auth_header = f"Bearer {token}"
        with self.assertRaises(HTTPException) as ctx:
            require_role(allowed_roles=["medico"], authorization=auth_header)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Acceso denegado (HTTP 403 Forbidden)", ctx.exception.detail)

if __name__ == "__main__":
    unittest.main()
