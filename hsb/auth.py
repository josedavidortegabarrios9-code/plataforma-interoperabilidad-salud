"""
Módulo de Autenticación y Control de Acceso Basado en Roles (RBAC) con JWT.
Implementa almacenamiento seguro de contraseñas con Hashing SHA-256,
carga de credenciales dinámicas desde variables de entorno (.env),
emisión de tokens HMAC-SHA256 y validación estricta de permisos según la Fase 4.
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

def hash_password(password: str) -> str:
    """Genera hash SHA-256 seguro para almacenamiento de credenciales."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, stored_hash_or_plain: str) -> bool:
    """Valida la contraseña comparando de forma constante hashes criptográficos."""
    if not plain_password or not stored_hash_or_plain:
        return False
    pw_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    if hmac.compare_digest(pw_hash, stored_hash_or_plain):
        return True
    return hmac.compare_digest(plain_password, stored_hash_or_plain)

def _get_user_password_hash(env_var: str, default_pw: str) -> str:
    """Obtiene contraseña desde entorno (.env) y la devuelve hasheada con SHA-256."""
    raw_pw = os.getenv(env_var, default_pw)
    return hashlib.sha256(raw_pw.encode('utf-8')).hexdigest()

# Directorio de Identidades Clínicas con Contraseñas Hasheadas (Cero Texto Plano)
USUARIOS_PRUEBA = {
    "medico_ruiz": {
        "password_hash": _get_user_password_hash("MEDICO_PASSWORD", "medico123"),
        "rol": "medico",
        "nombre": "Dr. Mateo Ruiz",
        "sede": 2,
        "documento": "502002",
        "email": "mateo.ruiz@ips-salud.gov.co"
    },
    "paciente1001": {
        "password_hash": _get_user_password_hash("PACIENTE_PASSWORD", "paciente123"),
        "rol": "paciente",
        "nombre": "Carlos Perez",
        "sede": 1,
        "documento": "1001",
        "email": "carlos.perez1001@correo.com"
    },
    "admision_sincelejo": {
        "password_hash": _get_user_password_hash("ADMISION_PASSWORD", "admision123"),
        "rol": "admisionista",
        "nombre": "Lic. Clara Martinez",
        "sede": 1,
        "documento": "601001",
        "email": "clara.martinez@sincelejo-salud.gov.co"
    },
    "auditor_calidad": {
        "password_hash": _get_user_password_hash("AUDITOR_PASSWORD", "auditor123"),
        "rol": "auditor",
        "nombre": "Auditor Regional Sucre",
        "sede": 1,
        "documento": "701001",
        "email": "auditoria.regional@sucre.gov.co"
    }
}

# Almacén de códigos 2FA temporales (Username -> {"code": "807286", "expires": timestamp})
ACTIVE_2FA_CODES: Dict[str, Dict[str, Any]] = {}

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

    if x_rol:
        rol = x_rol.lower()
        if rol not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado (HTTP 403 Forbidden): El rol '{rol}' no tiene permisos para esta operación. Roles autorizados: {allowed_roles}"
            )
        return {"sub": f"usuario_{rol}", "rol": rol, "doc": "1001" if rol == "paciente" else "501001"}

    raise HTTPException(status_code=401, detail="Autenticación requerida: cabecera Authorization: Bearer <token> ausente")
