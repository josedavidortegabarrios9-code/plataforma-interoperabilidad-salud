# Plataforma Distribuida de Interoperabilidad Clínica (Red de IPS)

[![FHIR R4](https://img.shields.io/badge/HL7-FHIR%20R4-blue.svg)](https://hl7.org/fhir/R4/)
[![FastAPI](https://img.shields.io/badge/HSB-FastAPI%20REST-green.svg)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose%20v2-2496ED.svg)](https://www.docker.com/)
[![Security](https://img.shields.io/badge/Auth-JWT%20%2B%202FA-blueviolet.svg)]()
[![Integrity](https://img.shields.io/badge/Audit-SHA--256%20Chain-orange.svg)]()
[![Status](https://img.shields.io/badge/Release-v1.0-brightgreen.svg)]()

Plataforma de interoperabilidad clínica para una red de Instituciones Prestadoras de Salud (IPS) distribuida en tres sedes regionales. Integra sistemas legados heterogéneos mediante un **Health Service Bus (HSB)**, normalización al estándar internacional **HL7 FHIR R4**, persistencia distribuida federada con transacciones **ACID**, autenticación con **Segundo Factor (2FA)**, control de acceso basado en roles (**RBAC**), tolerancia a fallos y auditoría criptográfica encadenada por **SHA-256**.

**Desarrolladores:**  
- **Jose Ortega Barrios**  
- **Raul Peralta Perez**  

---

## 🏥 1. Arquitectura de la Solución

La red asistencial opera de forma distribuida en tres sedes con sistemas independientes:

- **Sede 1 — Sincelejo:** Laboratorio clínico especializado (mensajería estándar HL7 v2 `ORU^R01` con codificación LOINC).
- **Sede 2 — Cartagena:** Urgencias y hospitalización (mensajería estándar HL7 v2 `ADT^A01` con codificación diagnóstica CIE-10).
- **Sede 3 — Corozal:** Consulta externa comunitaria (archivos planos legados estructurados en `CSV`).

```
                              ┌─────────────────────────────────────────┐
                              │           Frontend Web (SPA)            │
                              │ (Médico / Admisión / Auditor / Paciente)│
                              └────────────────────┬────────────────────┘
                                                   │ HTTP / JWT + 2FA
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             Health Service Bus (HSB Middleware)                                  │
│  ├── Ingesta Multiformato (HL7 v2, CSV, JSON REST)                                               │
│  ├── Validador Sintáctico y Semántico (Catálogos CIE-10, LOINC, Sexo, Tipo Doc)                   │
│  ├── Motor de Idempotencia Criptográfica (SHA-256 + MSH-10)                                      │
│  ├── Normalizador a Recursos FHIR R4 (Patient, Encounter, Condition, Observation)                │
│  ├── Control de Acceso RBAC (Tokens JWT HMAC-SHA256 con Mínimo Privilegio)                       │
│  ├── Auditoría Inmutable Encadenada (Hash Chaining SHA-256 Tamper-Evident)                       │
│  └── Colas de Reintento y Dead Letter Queue (DLQ) ante Caídas                                    │
└───────┬───────────────────────────────┬──────────────────────────────┬───────────────────────────┘
        │                               │                              │                           │
        ▼                               ▼                              ▼                           ▼
┌──────────────┐                ┌──────────────┐               ┌──────────────┐            ┌──────────────┐
│   pg_sede1   │                │   pg_sede2   │               │   pg_sede3   │            │  hapi_fhir   │
│ (Sincelejo)  │                │ (Cartagena)  │               │  (Corozal)   │            │ (Servidor R4)│
│ Puerto: 5431 │                │ Puerto: 5432 │               │ Puerto: 5433 │            │ Puerto: 8090 │
└──────────────┘                └──────────────┘               └──────────────┘            └──────────────┘
```

---

## ⚡ 2. Guía de Despliegue Rápido (Paso a Paso)

### Requisitos Previos
- **Docker** y **Docker Compose** instalados y en ejecución.
- **Git** instalado.

> [!NOTE]
> **¿Necesitas instalar o iniciar Python en tu máquina host?**
> **NO.** Todo el middleware (FastAPI, Uvicorn, parsers HL7, normalizador FHIR R4, ledger de auditoría) se compila y ejecuta **automáticamente dentro de Docker**. Al clonar y ejecutar `docker compose up --build -d`, el contenedor `hsb_service` inicializa el runtime de Python y todos los servicios sin requerir configuración previa en tu sistema operativo.

---

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/josedavidortegabarrios9-code/plataforma-interoperabilidad-salud.git
cd plataforma-interoperabilidad-salud
```

### Paso 2: Levantar el Clúster de Servicios
```bash
docker compose up --build -d
```
*Este comando descarga las imágenes oficiales, compila el contenedor del middleware HSB, inicializa las bases de datos de las 3 sedes y arranca el servidor HAPI FHIR R4.*

### Paso 3: Verificar que Todos los Nodos Están Saludables
```bash
docker compose ps
```
Todos los contenedores deben mostrar estado `Up` / `healthy`:
- `pg_sede1` (Sincelejo - Puerto 5431)
- `pg_sede2` (Cartagena - Puerto 5432)
- `pg_sede3` (Corozal - Puerto 5433)
- `hapi_fhir` (Servidor FHIR R4 - Puerto 8090)
- `hsb_service` (Middleware HSB + UI - Puerto 8000)

### Paso 4: Probar el Diagnóstico de Salud de la API
```bash
curl http://localhost:8000/health
```
Respuesta esperada:
```json
{
  "status": "healthy",
  "componentes": {
    "hsb_service": "UP",
    "nodo_sede1_sincelejo": "UP",
    "nodo_sede2_cartagena": "UP",
    "nodo_sede3_corozal": "UP",
    "hapi_fhir_server": "UP"
  }
}
```

### Paso 5: Abrir la Plataforma Web
Abre tu navegador web e ingresa a:  
👉 **`http://localhost:8000/`**

---

## 🔐 3. Autenticación y Control de Acceso (JWT + 2FA)

La plataforma utiliza autenticación multifactor obligatoria en dos etapas:

1. **Paso 1 — Credenciales:** Se ingresa usuario y contraseña.
2. **Paso 2 — Verificación de Segundo Factor (2FA):** El sistema emite un código criptográfico de 6 dígitos al correo institucional antes de generar el token JWT firmado con HMAC-SHA256.

### Roles y Políticas de Seguridad (Cero Credenciales Expuestas)

> [!IMPORTANT]
> **Gestión Segura de Secretos (Fase 4 & OWASP Top 10):**
> Siguiendo los principios de seguridad de la arquitectura distribuida, **ninguna contraseña en texto plano se almacena en el repositorio Git ni se muestra en la interfaz web**.
> 
> * Las credenciales de cada usuario se definen de forma aislada en el archivo local `.env` (a partir de la plantilla [`.env.example`](.env.example)).
> * El backend almacena y valida únicamente **Hashes Criptográficos SHA-256** mediante comparaciones de tiempo constante (`hmac.compare_digest`).
> * Si no se define un archivo `.env`, el sistema utiliza hashes de desarrollo precalculados.

| Rol Asistencial | Identificador / Usuario | Autenticación Multifactor | Vista Asignada en Plataforma | Permisos Asistenciales |
| :--- | :--- | :--- | :--- | :--- |
| **Médico Especialista** | `medico_ruiz` | Contraseña (`.env`) + Código 2FA (dinámico emitido a buzón) | Clínica Central | Consulta de historias unificadas de las 3 sedes y registro de diagnósticos CIE-10. |
| **Admisionista / Triage** | `admision_sincelejo` | Contraseña (`.env`) + Código 2FA (dinámico emitido a buzón) | Formulario Admisión | Admisión de pacientes y categorización de triage. **Bloqueo estricto a notas clínicas**. |
| **Auditor de Calidad** | `auditor_calidad` | Contraseña (`.env`) + Código 2FA (dinámico emitido a buzón) | Estado Nodos & Auditoría | Monitoreo de salud de nodos, simulación de caídas y verificación SHA-256. |
| **Paciente** | `paciente1001` | Contraseña (`.env`) + Código 2FA (dinámico emitido a buzón) | Portal Paciente | Resumen de sus atenciones y descarga de su Bundle FHIR R4 personal. |

---

## 🖥️ 4. Guía de Operación en la Interfaz Web

### A. Vista Admisionista (Admisión y Triage)
- Inicia sesión como `admision_sincelejo`.
- Se abre el **Formulario de Admisión de Paciente** estructurado en secciones:
  1. *Información del Paciente:* Documento (PID), Nombres, Apellidos, Fecha de Nacimiento y Género.
  2. *Información de Contacto:* Teléfono, Dirección y Correo electrónico.
  3. *Contacto de Emergencia:* Nombre del familiar, Teléfono y Parentesco.
  4. *Fecha de Admisión y Aseguradora:* Sede (Sincelejo, Cartagena, Corozal), Nivel de Triage (1 al 5) y EPS.
  5. *Información del Médico:* Profesional asignado y servicio.
- Al presionar **Enviar Formulario**, el HSB genera los recursos `Patient` y `Encounter` normalizados a FHIR R4.

### B. Vista Médico (Registro Clínico e Historia Unificada)
- Inicia sesión como `medico_ruiz`.
- En el panel de **Clínica Central**:
  - **`+ Crear historial medico`**: Permite ingresar diagnósticos CIE-10 (`J45.9`, `I10`, `E11.9`, etc.) y tecnologías en salud conectadas al HSB.
  - **`🔍 Consultar historial medico`**: Ingresa la cédula `1001` y presiona **Consultar**. Se desplegará la **Historia Clínica Unificada** con las atenciones combinadas de las 3 sedes (Sincelejo, Cartagena y Corozal) en una sola línea de tiempo.

### C. Vista Auditor (Métricas, Resiliencia y Auditoría SHA-256)
- Inicia sesión como `auditor_calidad`.
- **Métricas en tiempo real:** Muestra el total de mensajes procesados, entregados exitosos, duplicados detectados y tasa de fallos.
- **Tolerancia a fallos:** Haz clic en **Conmutar Caída** en la Sede 2 (Cartagena). La sede pasará a inactiva, pero la consulta de historias clínicas seguirá respondiendo en modo degradado resiliente con las demás sedes operativas.
- **Detector de alteraciones SHA-256:**
  - Presiona **Simular Alteración Maliciosa** (modifica un registro en la base de datos).
  - Presiona **Re-verificar**. El sistema alertará de inmediato que la integridad criptográfica fue quebrada.

### D. Vista Paciente (Descarga de Historia FHIR R4)
- Inicia sesión como `paciente1001`.
- Consulta su resumen personal de atenciones y permite hacer clic en **Descargar mi Historia en FHIR R4 (JSON)** para obtener el Bundle interoperable oficial.

---

## 🔍 5. Búsqueda y Verificación de Pacientes desde la Terminal (PostgreSQL & HSB)

Durante una demostración técnica o sustentación, puedes consultar directamente la persistencia en las bases de datos de cada sede y validar que los registros existan tanto en los motores relacionales como en la capa FHIR unificada.

### A. Consultar Registros Directamente en los Contenedores PostgreSQL

Cada sede cuenta con su base de datos independiente. Ejecuta estos comandos en tu terminal de Linux:

#### 1. Buscar un paciente específico por Cédula / Documento (ejemplo: `1001`):
```bash
# Consultar en Sede 1 - Sincelejo (Laboratorio Clínico)
docker exec -it pg_sede1 psql -U postgres -d historia_clinica_sede1 -c \
  "SELECT u.numero_documento, u.primer_nombre, u.primer_apellido, a.id_atencion, a.fecha_hora_ingreso, a.causa_atencion FROM usuario u LEFT JOIN atencion a ON u.id_usuario = a.id_usuario WHERE u.numero_documento = '1001';"

# Consultar en Sede 2 - Cartagena (Urgencias / Hospitalización)
docker exec -it pg_sede2 psql -U postgres -d historia_clinica_sede2 -c \
  "SELECT u.numero_documento, u.primer_nombre, u.primer_apellido, a.id_atencion, a.fecha_hora_ingreso, a.causa_atencion FROM usuario u LEFT JOIN atencion a ON u.id_usuario = a.id_usuario WHERE u.numero_documento = '1001';"

# Consultar en Sede 3 - Corozal (Consulta Externa Comunitaria)
docker exec -it pg_sede3 psql -U postgres -d historia_clinica_sede3 -c \
  "SELECT u.numero_documento, u.primer_nombre, u.primer_apellido, a.id_atencion, a.fecha_hora_ingreso, a.causa_atencion FROM usuario u LEFT JOIN atencion a ON u.id_usuario = a.id_usuario WHERE u.numero_documento = '1001';"
```

#### 2. Listar los últimos pacientes registrados en una sede:
```bash
# Ver los últimos 5 pacientes registrados en la Sede 2 (Cartagena)
docker exec -it pg_sede2 psql -U postgres -d historia_clinica_sede2 -c \
  "SELECT u.id_usuario, u.numero_documento, u.primer_nombre, u.primer_apellido, u.fecha_nacimiento, u.cod_sexo, a.id_atencion, a.fecha_hora_ingreso FROM usuario u JOIN atencion a ON u.id_usuario = a.id_usuario ORDER BY a.fecha_hora_ingreso DESC LIMIT 5;"
```

#### 3. Consultar diagnósticos CIE-10 asignados a un paciente:
```bash
docker exec -it pg_sede2 psql -U postgres -d historia_clinica_sede2 -c \
  "SELECT d.id_atencion, d.cod_cie10, c.descripcion, d.tipo FROM diagnostico d LEFT JOIN cat_cie10 c ON d.cod_cie10 = c.cod_cie10;"
```

---

### B. Consultar la Historia Clínica Unificada vía API HSB (HTTP / REST)

Para consultar la historia combinada de un paciente en las 3 sedes mediante la terminal:

```bash
# Consulta como Médico (acceso completo a diagnósticos y atenciones multisede)
curl -s -H "X-Rol: medico" http://localhost:8000/paciente/1001/historia-unificada | jq .
```
*Salida:* Devuelve un JSON consolidado con el perfil demográfico del paciente, la cobertura FHIR (100%), las atenciones ordenadas cronológicamente y el estado operativo de cada sede consultada.

---

### C. Descargar y Validar el Bundle FHIR R4 desde la Terminal

Para inspeccionar el recurso interoperable oficial generado por el HSB:

```bash
# Obtener Bundle de transacción FHIR R4
curl -s http://localhost:8000/paciente/1001/bundle | jq '{resourceType: .resourceType, type: .type, total_entries: (.entry | length)}'
```
*Salida esperada:*
```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "total_entries": 4
}
```

---

## 📡 6. Protocolo de Pruebas y Casos de Aceptación Verificados (Demostración en Vivo)

A continuación se presenta el protocolo completo de pruebas de aceptación y tolerancia a fallos ejecutado y validado en la plataforma:

---

### Caso 1: Ingesta HL7 v2 y Creación en Servidor HAPI FHIR Real (No Mocks)
Envía un mensaje clínico `ADT^A01` nuevo al HSB con rol médico:
```bash
sed 's/MSG-0001/MSG-1001/' tests/01_adt_a01_valido_sede2.hl7 | curl -s -X POST http://localhost:8000/hsb/hl7 -H "Content-Type: text/plain" -H "X-Rol: medico" --data-binary @- | jq .
```
*Salida real obtenida:*
```json
{
  "estado": "entregado",
  "id_mensaje": "MSG-1001",
  "documento": "1007",
  "sede": 2,
  "fhir_patient_id": "pac-1007",
  "recursos_creados": [
    "pac-1007",
    "enc-V-S2-0101",
    "cond-1007-J45.9"
  ],
  "latencia_ms": 1315.23
}
```
*Comprobación en HAPI FHIR:* El recurso `Patient/pac-1007` puede consultarse directamente en el servidor R4:
```bash
curl -s http://localhost:8090/fhir/Patient/pac-1007 | jq .
```

---

### Caso 2: Idempotencia Criptográfica (Prevención de Duplicados)
Al reenviar el mismo mensaje o un mensaje con un `id_mensaje` ya procesado:
```bash
curl -s -X POST http://localhost:8000/hsb/hl7 -H "Content-Type: text/plain" -H "X-Rol: medico" --data-binary @tests/01_adt_a01_valido_sede2.hl7 | jq .
```
*Salida real obtenida:*
```json
{
  "estado": "duplicado",
  "id_mensaje": "MSG-0001",
  "mensaje": "Mensaje MSG-0001 ya fue procesado previamente. No se crean duplicados.",
  "documento": "1007",
  "sede": 2
}
```

---

### Caso 3: Tolerancia a Fallos ante Caída de Sede (Degradación Elegante)
Simula la caída de la base de datos de Cartagena (`pg_sede2`) y consulta la historia clínica unificada del paciente:
```bash
# 1. Tumbar nodo de Sede 2
docker stop pg_sede2

# 2. Consultar historia unificada
curl -s -H "X-Rol: medico" "http://localhost:8000/paciente/1007/historia-unificada" | jq .
```
*Salida real obtenida (el sistema no se cae, informa sedes activas y responde con degradación tolerante):*
```json
{
  "paciente": {
    "documento": "1007",
    "tipo_documento": "CC",
    "nombre": "Andrea",
    "apellido": "Rojas",
    "nacimiento": "19900214",
    "sexo": "F",
    "fhir_patient_id": "pac-1007"
  },
  "cobertura_fhir": "100%",
  "total_atenciones": 0,
  "atenciones": [],
  "sedes_consultadas": 2,
  "sedes_activas": [
    {
      "id_sede": 1,
      "nombre": "Sincelejo",
      "estado": "OPERATIVA"
    },
    {
      "id_sede": 3,
      "nombre": "Corozal",
      "estado": "OPERATIVA"
    }
  ],
  "sedes_inactivas": [
    {
      "id_sede": 2,
      "nombre": "Cartagena",
      "estado": "CAIDA_NO_DISPONIBLE"
    }
  ],
  "degradacion_tolerante": true
}
```

---

### Caso 4: Tolerancia a Fallos ante Caída de HAPI FHIR (Desvío a DLQ sin Falsos Positivos)
Simula la caída del servidor central HAPI FHIR e intenta procesar un nuevo mensaje clínico:
```bash
# 1. Tumbar servidor FHIR
docker stop hapi_fhir

# 2. Enviar mensaje nuevo
sed 's/MSG-0001/MSG-9999/' tests/01_adt_a01_valido_sede2.hl7 | curl -s -X POST http://localhost:8000/hsb/hl7 -H "Content-Type: text/plain" -H "X-Rol: medico" --data-binary @- | jq .
```
*Salida real obtenida (el HSB reintenta, no dice falso positivo y desvía a la DLQ):*
```json
{
  "estado": "muerto",
  "id_mensaje": "MSG-9999",
  "mensaje": "Mensaje no pudo entregarse a HAPI FHIR tras reintentos y fue desviado a la cola de mensajes muertos (DLQ): HAPI FHIR no disponible o rechazó el Bundle"
}
```

---

### Caso 5: Auto-recuperación (Self-Healing)
Restaura los contenedores caídos. El worker asíncrono en segundo plano (`_worker_reintentos`) del HSB reconecta automáticamente sin necesidad de reiniciar la API:
```bash
docker start pg_sede2 hapi_fhir
```

---

### Caso 6: Verificación de la Cadena Criptográfica de Auditoría (SHA-256 Tamper-Evident)
Tras ejecutar ingestas, caídas y recuperaciones, valida la inmutabilidad del registro de eventos:
```bash
curl -s http://localhost:8000/audit/verify | jq .
```
*Salida real obtenida:*
```json
{
  "integro": true,
  "total_eventos": 4,
  "ultimo_hash": "5f8de0df327686913cbdb5608e03d8cbb7a25be5f0665066938e0bc746c31c3a",
  "mensaje": "Integridad criptográfica verificada: 0 alteraciones detectadas"
}
```

---

### Caso 7: Ingesta de Laboratorio HL7 v2 ORU^R01 (Sede 1 - Sincelejo)
```bash
curl -s -X POST http://localhost:8000/hsb/hl7 -H "Content-Type: text/plain" -H "X-Rol: medico" --data-binary @tests/02_oru_r01_laboratorio_sede1.hl7 | jq .
```
*Salida esperada:* `estado: entregado` con recurso de observación LOINC `718-7` (Hemoglobina: 13.8 g/dL).

---

### Caso 8: Ingesta por Lotes de Archivo CSV Legado (Sede 3 - Corozal)
```bash
curl -s -X POST "http://localhost:8000/hsb/csv?sede=3" -H "Content-Type: text/plain" -H "X-Rol: medico" --data-binary @tests/04_sede3_legado.csv | jq .
```
*Salida esperada:*
```json
{
  "total_lineas": 5,
  "entregados": 3,
  "rechazados": 2
}
```

---

### Caso 9: Rechazo de Mensaje HL7 Malformado (Validación Sintáctica)
```bash
curl -s -X POST http://localhost:8000/hsb/hl7 -H "Content-Type: text/plain" -H "X-Rol: medico" --data-binary @tests/03_adt_a01_invalido.hl7 | jq .
```
*Salida esperada:* Código `HTTP 422 Unprocessable Entity` con detalle de los campos rechazados (documento no numérico, sexo no válido, etc.).

---

## 🛡️ 7. Pruebas de Seguridad y Control de Acceso (RBAC)

### Rechazo de Acceso No Autorizado (HTTP 403 Forbidden)

1. Obtener token de la admisionista:
```bash
# Iniciar sesión con el usuario admisionista (la contraseña se toma de las variables de entorno locales)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admision_sincelejo","password":"'${ADMISION_PASSWORD:-admision123}'"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
```

2. Intentar consultar historia clínica médica con ese token:
```bash
curl -i http://localhost:8000/paciente/1001/historia-unificada \
  -H "Authorization: Bearer $TOKEN"
```
*Respuesta:*
```text
HTTP/1.1 403 Forbidden
{"detail": "Acceso denegado (HTTP 403 Forbidden): El personal de Admisión y Triage NO está autorizado para consultar notas ni diagnósticos clínicos."}
```

---

## 🔍 8. Verificación de Auditoría Criptográfica (SHA-256)

1. **Verificar cadena íntegra:**
```bash
curl -s http://localhost:8000/audit/verify | jq .
```
*Resultado:*
```json
{
  "integro": true,
  "total_eventos": 4,
  "ultimo_hash": "...",
  "mensaje": "Integridad criptográfica verificada: 0 alteraciones detectadas"
}
```

2. **Simular alteración de registro (Tamper Detection):**
```bash
curl -s -X POST "http://localhost:8000/audit/tamper?evento_id=1" | jq .
```

3. **Comprobar detección inmediata de manipulación:**
```bash
curl -s http://localhost:8000/audit/verify | jq .
```
*Resultado:*
```json
{
  "integro": false,
  "evento_alterado_id": 1,
  "indice": 0,
  "motivo": "Contenido modificado en evento 1: el hash actual no coincide con los datos sellados"
}
```

---

## 🧪 9. Ejecución de la Suite de Pruebas Automatizadas

La plataforma cuenta con **30 pruebas automáticas exhaustivas** divididas en pruebas sintácticas, semánticas, normalización FHIR R4, seguridad RBAC/2FA e integración del HSB. Puedes ejecutarlas de dos formas:

### Opción A (Recomendada — Directamente en el contenedor Docker, sin instalar Python en tu máquina):
```bash
docker exec -it hsb_service python -m unittest discover -s tests -v
```
*(No requiere crear entornos virtuales ni instalar dependencias en el host; utiliza el entorno preconfigurado dentro del contenedor `hsb_service`)*.

---

### Opción B (Desde el entorno virtual local de Ubuntu / Host):
```bash
# 1. Crear entorno virtual si aún no existe
python3 -m venv venv

# 2. Activar el entorno virtual
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la suite completa de 30 tests
python -m unittest discover -s tests -v
```

*Salida esperada:*
```text
test_01_hash_password_sha256 (test_auth.TestAuthSecurity.test_01_hash_password_sha256) ... ok
test_02_verify_password_valido_e_invalido (test_auth.TestAuthSecurity.test_02_verify_password_valido_e_invalido) ... ok
test_03_jwt_creacion_y_validacion (test_auth.TestAuthSecurity.test_03_jwt_creacion_y_validacion) ... ok
...
test_11_tolerancia_fallos_sede_caida_con_degradacion (test_hsb_integration.TestHSBIntegration.test_11_tolerancia_fallos_sede_caida_con_degradacion) ... ok
----------------------------------------------------------------------
Ran 30 tests in 0.508s

OK
```

---

## 🛠️ 10. Guía de Solución de Problemas y Errores Comunes (Troubleshooting)

A continuación se detallan los incidentes más comunes al desplegar o probar la plataforma y su solución paso a paso:

### 1. HAPI FHIR tarda en responder o retorna `503 Service Unavailable` / `Connection Refused`
- **Causa:** El contenedor oficial `hapi_fhir` (basado en Java/Tomcat con Spring Boot y JPA) realiza migraciones iniciales de base de datos y levantamiento del metamodelo FHIR R4. En máquinas virtuales de desarrollo, este arranque suele tardar entre **2 y 4 minutos**.
- **Diagnóstico:** Revisa el log de inicialización de HAPI:
  ```bash
  docker logs -f hapi_fhir
  ```
  Espera hasta que aparezca la línea:
  `INFO ... Started ServerConnector@... {HTTP/1.1, (http/1.1)}{0.0.0.0:8080}`
- **Solución:**
  Verifica directamente el endpoint de metadatos hasta recibir `HTTP 200`:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8090/fhir/metadata
  ```
  Una vez retorne `200`, el servidor está 100% operativo para recibir bundles.

### 2. Error Tomcat `400 Bad Request` por violaciones de RFC 1123 en nombres de Host
- **Causa:** En versiones recientes de Apache Tomcat/HAPI FHIR, los nombres de host internos de Docker que contienen guiones bajos (como `http://hapi_fhir:8080/fhir`) son rechazados con `HTTP 400` porque el RFC 1123 prohíbe guiones bajos en el encabezado HTTP `Host`.
- **Solución integrada:**
  El middleware HSB ya inyecta de forma transparente el encabezado estándar:
  ```python
  headers={"Host": "localhost:8080", "Content-Type": "application/fhir+json"}
  ```
  Además, `docker-compose.yml` expone los alias de red `hapifhir` y `hapi-fhir`.

### 3. Los cambios en el código Python no se reflejan tras modificar archivos
- **Causa:** Ejecutar `docker compose restart hsb_service` solo reinicia el proceso dentro del contenedor con la imagen compilada previamente; **no actualiza el código**.
- **Solución obligatoria:**
  Reconstruye la imagen del servicio con:
  ```bash
  docker compose up -d --build hsb_service
  ```

### 4. Conflicto de puertos en el Host (5431, 5432, 5433, 8000, 8090)
- **Causa:** Existe una instancia local de PostgreSQL activa en tu máquina en el puerto `5432`, o un servidor web local ocupando el puerto `8000` o `8090`.
- **Diagnóstico:**
  ```bash
  sudo ss -tulpn | grep -E ':(5431|5432|5433|8000|8090)'
  ```
- **Solución:**
  - Si es PostgreSQL local: `sudo systemctl stop postgresql`
  - Si necesitas mapear a puertos libres, crea tu archivo `.env` local (`cp .env.example .env`) y personaliza:
    ```bash
    SEDE2_PORT=5435
    HSB_PORT=8001
    HAPI_PORT=8095
    ```

### 5. Error de permisos de Docker en Linux (`permission denied while trying to connect to Docker daemon`)
- **Causa:** Tu usuario de Ubuntu no pertenece al grupo `docker`.
- **Solución:**
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

### 6. Archivo de configuración `.env` no encontrado
- **Causa:** Por lineamientos de seguridad OWASP y Git, `.env` está ignorado en `.gitignore`.
- **Solución:**
  ```bash
  cp .env.example .env
  ```
  El HSB cuenta con resolución defensiva en cascada: si `.env` no está presente, lee `.env.example` y variables del sistema sin detener la ejecución.

### 7. Reiniciar el entorno completamente limpio desde cero
- **Causa:** Si deseas purgar todos los datos de pruebas previas, colas y transacciones para una sustentación limpia:
- **Solución:**
  ```bash
  # 1. Apagar contenedores y eliminar volúmenes
  docker compose down -v
  
  # 2. Levantar y compilar todo desde cero
  docker compose up -d --build
  
  # 3. Esperar 1 minuto y verificar estado
  docker compose ps
  ```

---

## 📁 11. Estructura del Proyecto

```
plataforma-interoperabilidad-salud/
├── db/                   # Esquemas SQL, catálogos y datos sintéticos de las 3 sedes
│   ├── init_schema.sql   # Esquema relacional asistencial
│   ├── catalogs.sql      # Catálogos oficiales (CIE-10, LOINC, Sexo, Tipo Doc)
│   ├── seed_sede1.sql    # Datos Sede 1 (Sincelejo - Laboratorio)
│   ├── seed_sede2.sql    # Datos Sede 2 (Cartagena - Urgencias)
│   └── seed_sede3.sql    # Datos Sede 3 (Corozal - Consulta Externa)
├── docs/                 # Documentación técnica, diagramas y especificaciones
├── fhir/                 # Especificación de recursos y normalizador HL7 FHIR R4
│   └── normalizer.py     # Construcción de Bundles Transaction deterministas
├── hsb/                  # Health Service Bus (Middleware en FastAPI)
│   ├── main.py           # API REST, router de sedes, observabilidad e interfaz web
│   ├── parser.py         # Parsers HL7 v2 y CSV con validación de contratos
│   ├── auth.py           # Gestión de JWT HMAC-SHA256 y matriz RBAC
│   ├── audit.py          # Ledger de auditoría con encadenamiento SHA-256
│   ├── database.py       # Capa de persistencia distribuida federada (3 sedes)
│   └── Dockerfile        # Definición multicapa del contenedor del HSB
├── tests/                # Fixtures oficiales de prueba y suites de testing
│   ├── 01_adt_a01_valido_sede2.hl7
│   ├── 02_oru_r01_laboratorio_sede1.hl7
│   ├── 03_adt_a01_invalido.hl7
│   ├── 04_sede3_legado.csv
│   ├── test_auth.py            # Pruebas de seguridad JWT, RBAC y hashing
│   ├── test_normalizer.py      # Pruebas de normalización FHIR R4
│   ├── test_parser_contracts.py# Pruebas de validación sintáctica/semántica
│   └── test_hsb_integration.py # Pruebas de integración, DLQ y resiliencia
├── .env.example          # Plantilla de variables de entorno seguras
├── requirements.txt      # Dependencias Python del proyecto
└── docker-compose.yml    # Orquestación multicontenedor de la red distribuida
```
