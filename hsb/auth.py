"""
Módulo de Autenticación y Control de Acceso Basado en Roles (RBAC) con JWT.
Implementa emisión de tokens HMAC-SHA256 y validación estricta de permisos según la Fase 4.
"""

import hmac
import hashlib
import base64
import json
import time
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException, Header

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_clinical_interoperability_key_2026")

# Base de Usuarios de Prueba (según README oficial del parcial)
USUARIOS_PRUEBA = {
    "medico_ruiz": {
        "password": "medico123",
        "rol": "medico",
        "nombre": "Dr. Mateo Ruiz",
        "sede": 2,
        "documento": "502002"
    },
    "paciente1001": {
        "password": "paciente123",
        "rol": "paciente",
        "nombre": "Carlos Perez",
        "sede": 1,
        "documento": "1001"
    },
    "admision_sincelejo": {
        "password": "admision123",
        "rol": "admisionista",
        "nombre": "Lic. Clara Martinez",
        "sede": 1,
        "documento": "601001"
    },
    "auditor_calidad": {
        "password": "auditor123",
        "rol": "auditor",
        "nombre": "Auditor Regional Sucre",
        "sede": 1,
        "documento": "701001"
    }
}

# Matriz de Permisos Estrictos por Rol (Fase 4 de la Guía)
PERMISOS_ROL = {
    "paciente": {
        "ver_propia_historia": True,
        "ver_otra_historia": False,
        "abrir_atencion": False,
        "registrar_diagnostico": False,
        "ver_estado_plataforma": False,
        "descargar_bundle_propio": True
    },
    "admisionista": {
        "ver_propia_historia": False,
        "ver_otra_historia": False,  # NO PUEDE VER HISTORIA CLÍNICA DETALLADA
        "abrir_atencion": True,
        "registrar_diagnostico": False,
        "ver_estado_plataforma": False,
        "descargar_bundle_propio": False
    },
    "medico": {
        "ver_propia_historia": True,
        "ver_otra_historia": True,
        "abrir_atencion": False,
        "registrar_diagnostico": True,
        "ver_estado_plataforma": True,
        "descargar_bundle_propio": True
    },
    "auditor": {
        "ver_propia_historia": False,
        "ver_otra_historia": True,  # Solo para reporte de calidad
        "abrir_atencion": False,
        "registrar_diagnostico": False,
        "ver_estado_plataforma": True,
        "descargar_bundle_propio": True
    }
}

class JWTManager:
    @staticmethod
    def _b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    @staticmethod
    def _b64_decode(data_str: str) -> bytes:
        padding = '=' * (4 - (len(data_str) % 4)) if (len(data_str) % 4) != 0 else ''
        return base64.urlsafe_b64decode(data_str + padding)

    @classmethod
    def create_token(cls, username: str, rol: str, documento: str, expires_in_seconds: int = 86400) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": username,
            "rol": rol,
            "doc": documento,
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in_seconds
        }

        header_b64 = cls._b64_encode(json.dumps(header).encode('utf-8'))
        payload_b64 = cls._b64_encode(json.dumps(payload).encode('utf-8'))
        signature_raw = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(JWT_SECRET.encode('utf-8'), signature_raw, hashlib.sha256).digest()
        sig_b64 = cls._b64_encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Token JWT con formato inválido")

        header_b64, payload_b64, sig_b64 = parts
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), f"{header_b64}.{payload_b64}".encode('utf-8'), hashlib.sha256).digest()
        actual_sig = cls._b64_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(status_code=401, detail="Firma de token JWT inválida o manipulada")

        payload = json.loads(cls._b64_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token JWT expirado")

        return payload

def require_role(allowed_roles: list, authorization: Optional[str] = Header(None), x_rol: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Middleware de seguridad RBAC: valida el token Bearer o el header de prueba X-Rol.
    Si el usuario no tiene uno de los roles permitidos, rechaza con HTTP 403 Forbidden.
    """
    # 1. Si viene por Authorization Bearer Token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        user_info = JWTManager.verify_token(token)
        rol = user_info.get("rol")
        if rol not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado (HTTP 403 Forbidden): El rol '{rol}' no tiene permisos para esta operación asistencial. Se requiere uno de: {allowed_roles}"
            )
        return user_info

    # 2. Si viene por header directo (para pruebas automáticas o conmutación rápida)
    if x_rol:
        rol = x_rol.lower()
        if rol not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado (HTTP 403 Forbidden): El rol '{rol}' no tiene permisos para esta operación. Roles autorizados: {allowed_roles}"
            )
        return {"sub": f"usuario_{rol}", "rol": rol, "doc": "1001" if rol == "paciente" else "501001"}

    # 3. Si no viene credencial
    raise HTTPException(status_code=401, detail="Autenticación requerida: cabecera Authorization: Bearer <token> ausente")
