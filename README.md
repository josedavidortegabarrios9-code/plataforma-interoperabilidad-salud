# Plataforma Distribuida de Interoperabilidad Clínica (Red de IPS)

[![FHIR R4](https://img.shields.io/badge/HL7-FHIR%20R4-blue.svg)](https://hl7.org/fhir/R4/)
[![FastAPI](https://img.shields.io/badge/HSB-FastAPI%20REST-green.svg)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose%20v2-2496ED.svg)](https://www.docker.com/)
[![Integrity](https://img.shields.io/badge/Audit-SHA--256%20Chain-orange.svg)]()
[![Status](https://img.shields.io/badge/Release-v1.0-brightgreen.svg)]()

**Asignatura:** Sistemas Distribuidos  
**Institución:** Universidad Antonio José de Sucre (UAJS)  
**Docente:** Ing. Jaider Reyes Herazo  
**Equipo de Estudiantes:**  
- **Jose Ortega Barrios**  
- **Raul Peralta Perez**  
**Versión de Entrega:** `v1.0` (Aprobada con todos los criterios RF1 a RF6 y RNF)

---

## 🏥 1. Descripción del Escenario

Plataforma distribuida de interoperabilidad clínica para una red de Instituciones Prestadoras de Salud (IPS) distribuida en tres sedes regionales:
- **Sede 1 — Sincelejo:** Laboratorio clínico ambulatorio (emite mensajería estándar HL7 v2 `ORU^R01` con códigos LOINC).
- **Sede 2 — Cartagena:** Urgencias y hospitalización médica (emite mensajería HL7 v2 `ADT^A01` con codificación CIE-10).
- **Sede 3 — Corozal:** Consulta externa comunitaria (emite archivos planos legados delimitados por punto y coma `CSV`).

La plataforma integra los sistemas legados sin reemplazarlos mediante un **Health Service Bus (HSB)**, normalización al estándar internacional **HL7 FHIR R4**, persistencia distribuida federada con transacciones **ACID**, auditoría criptográfica encadenada por **SHA-256** y un **Frontend con 4 Vistas por Rol**.

---

## 📁 2. Estructura del Repositorio

El proyecto cumple la estructura exigida en la guía oficial del parcial:

```
plataforma-interoperabilidad-salud/
├── app/                  # Recursos y componentes del frontend web
├── db/                   # Esquemas SQL, catálogos e inicialización de los 3 nodos PostgreSQL
│   ├── init_schema.sql   # Esquema clínico relacional
│   ├── catalogs.sql      # Catálogos oficiales y mapeos terminológicos
│   ├── seed_sede1.sql    # Datos sintéticos Sede 1 (Sincelejo)
│   ├── seed_sede2.sql    # Datos sintéticos Sede 2 (Cartagena)
│   └── seed_sede3.sql    # Datos sintéticos Sede 3 (Corozal)
├── docs/                 # Informes técnicos formales según la Plantilla v7
│   ├── fase1_informe_arquitectura_uml.md    # Resumen, UML y Arquitectura
│   ├── fase2_datos_distribuidos_fhir.md    # Estado del arte (APA 7), CAP y ACID
│   ├── fase3_hsb_middleware.md             # Ingesta, Idempotencia y DLQ
│   ├── fase4_seguridad_resiliencia.md      # RBAC, Auditoría SHA-256 y Caída
│   └── fase5_informe_final_sustentacion.md # Prototipo y Guion de 15 min
├── fhir/                 # Normalizador y especificación HL7 FHIR R4
│   └── normalizer.py     # Transforma datos a Bundles Transaction PUT deterministas
├── hsb/                  # Health Service Bus (Middleware central en FastAPI)
│   ├── main.py           # API REST, orquestador, 4 vistas web y observabilidad
│   ├── parser.py         # Parser y validador de HL7 v2 y CSV según LEEME.md
│   ├── audit.py          # Ledger de auditoría con cadena de hashes SHA-256
│   ├── Dockerfile        # Contenedor del HSB
│   └── requirements.txt  # Dependencias Python
├── infra/                # Configuraciones adicionales de infraestructura
├── tests/                # Suites de prueba automatizadas y fixtures oficiales
│   ├── 01_adt_a01_valido_sede2.hl7         # Contrato HL7 válido Sede 2
│   ├── 02_oru_r01_laboratorio_sede1.hl7     # Contrato HL7 laboratorio Sede 1
│   ├── 03_adt_a01_invalido.hl7              # Contrato HL7 inválido (3 motivos)
│   ├── 04_sede3_legado.csv                  # Contrato CSV (3 válidos, 2 rechazados)
│   ├── test_normalizer.py                  # Pruebas unitarias FHIR R4 (6 tests)
│   ├── test_parser_contracts.py            # Pruebas de contratos LEEME.md (4 tests)
│   └── test_hsb_integration.py             # Pruebas extremo a extremo (10 tests)
└── docker-compose.yml    # Orquestación de toda la plataforma
```

---

## ⚡ 3. Guía de Arranque Rápido

### Requisitos Previos
- **Docker** y **Docker Compose** instalados (o Docker Desktop activo en Windows / Linux).
- **Git** para clonar el repositorio.

---

### Opción A: Despliegue Oficial en Contenedores (Un Solo Comando)

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/josedavidortegabarrios9-code/plataforma-interoperabilidad-salud.git
   cd plataforma-interoperabilidad-salud
   ```

2. **Levantar todo el clúster:**
   ```bash
   docker compose up --build -d
   ```

3. **Verificar el estado de los contenedores:**
   ```bash
   docker compose ps
   ```
   *Todos los servicios (`pg_sede1`, `pg_sede2`, `pg_sede3`, `hapi_fhir`, `hsb_service`) deben figurar en estado `Up` / `healthy`.*

4. **Abrir la plataforma web:**  
   Accede desde tu navegador a: 👉 **`http://localhost:8000/`**

---

### Opción B: Ejecución Local en Python (Sin Docker)

Si deseas probar la lógica y el frontend directamente en tu máquina:

```bash
# 1. Instalar dependencias
pip install -r hsb/requirements.txt

# 2. Ejecutar el HSB y las 4 Vistas
python hsb/main.py
```
Abre en el navegador: 👉 **`http://localhost:8000/`**

---

## 👥 4. Usuarios de Prueba y Roles de Acceso (RBAC)

El frontend dispone de un selector dinámico en la barra superior para cambiar de rol y comprobar los permisos:

| Rol | Identidad | Permisos Permitidos | Restricción Estricta (HTTP 403) |
| :--- | :--- | :--- | :--- |
| **Médico** | `medico_ruiz` | Consulta unificada completa de las 3 sedes, registrar diagnósticos CIE-10 y egresos. | Alterar eventos de auditoría. |
| **Paciente** | `paciente1001` | Ver su propia historia unificada, descargar Bundle FHIR R4 y ver auditoría de accesos. | Modificar historias o ver otros pacientes. |
| **Admisionista** | `admision_sincelejo` | Buscar pacientes, detectar duplicados inter-sedes y abrir atenciones con nivel de triage. | **Ver diagnósticos clínicos o notas médicas.** |
| **Auditor** | `auditor_calidad` | Reporte de cobertura, métricas de rendimiento, tablero de nodos y verificador de integridad. | Editar contenido asistencial. |

---

## 🧪 5. Comandos de Prueba para Sustentación en Vivo (`curl`)

El docente puede verificar el cumplimiento de los contratos en tiempo real ejecutando estos comandos:

### 1. Ingesta de mensaje válido HL7 v2 (Sede 2 - Cartagena)
```bash
curl -X POST http://localhost:8000/hsb/hl7 \
  -H "Content-Type: text/plain" \
  --data-binary @tests/01_adt_a01_valido_sede2.hl7
```
*Resultado:* `estado: entregado`, Patient 1007, Encounter y Condition J45.9 en Sede 2. Cobertura FHIR sube a 100%.

### 2. Demostración de Idempotencia (Reenvío idéntico)
```bash
curl -X POST http://localhost:8000/hsb/hl7 \
  -H "Content-Type: text/plain" \
  --data-binary @tests/01_adt_a01_valido_sede2.hl7
```
*Resultado:* `estado: duplicado`. Gracias al hash SHA-256 y `MSH-10`, **no se crea ningún registro duplicado**.

### 3. Ingesta de mensaje inválido (Rechazado con 3 motivos exactos)
```bash
curl -X POST http://localhost:8000/hsb/hl7 \
  -H "Content-Type: text/plain" \
  --data-binary @tests/03_adt_a01_invalido.hl7
```
*Resultado:* Código HTTP 422 con motivos: `documento no numérico`, `sexo no válido`, `diagnóstico sin mapeo a CIE-10`.

### 4. Ingesta de CSV legado (Sede 3 - Corozal)
```bash
curl -X POST "http://localhost:8000/hsb/csv?sede=3" \
  -H "Content-Type: text/plain" \
  --data-binary @tests/04_sede3_legado.csv
```
*Resultado:* 3 entregados (1008, 1009, 1010) y 2 rechazados (1011 sin mapeo y 12 con doc de 2 dígitos).

### 5. Verificación de Integridad Criptográfica (Tamper Detection)
```bash
curl -s http://localhost:8000/audit/verify
```
*Resultado:* `integro: true`, 0 alteraciones detectadas en los hashes SHA-256.

### 6. Prueba de Resiliencia ante Caída de Sede (Tolerancia a Fallos Parciales)
```bash
# Simular caída de Sede 2 (Cartagena)
curl -X POST "http://localhost:8000/test/toggle-sede?sede_id=2"

# Consultar paciente 1001 (responde con sedes activas 1 y 3 sin dar error 500)
curl -s "http://localhost:8000/paciente/1001/historia-unificada" -H "X-Rol: medico"
```

---

## 🚦 6. Ejecución de la Batería Completa de Pruebas Automatizadas

Para validar las **16 pruebas unitarias y de integración** automáticas:

```bash
# 1. Pruebas de Contratos de LEEME.md (4 tests)
python tests/test_parser_contracts.py

# 2. Pruebas del Normalizador FHIR R4 (6 tests)
python tests/test_normalizer.py

# 3. Pruebas de Integración Extremo a Extremo (10 tests)
python tests/test_hsb_integration.py
```

*Salida esperada:* `Ran 10 tests in 0.15s - OK`.

---

## 📚 7. Documentación Formal de Entrega (Plantilla v7)

- [Fase 1: Análisis, Modelado UML y Arquitectura](docs/fase1_informe_arquitectura_uml.md)
- [Fase 2: Datos Distribuidos y FHIR R4](docs/fase2_datos_distribuidos_fhir.md)
- [Fase 3: HSB y Middleware de Integración](docs/fase3_hsb_middleware.md)
- [Fase 4: Seguridad, Auditoría Criptográfica y Resiliencia](docs/fase4_seguridad_resiliencia.md)
- [Fase 5: Prototipo Final y Guion Oficial de Sustentación](docs/fase5_informe_final_sustentacion.md)

---

## 🏷️ 8. Etiquetas de Versión (Releases)
- `v0.1-fase1`: Entrega formal de la Fase 1.
- `v0.2-fase2`: Entrega formal de la Fase 2.
- `v1.0`: **Versión de entrega final de la plataforma completa y sustentación.**
