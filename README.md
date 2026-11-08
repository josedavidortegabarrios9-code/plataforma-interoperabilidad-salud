# Plataforma Distribuida de Interoperabilidad Clínica (Red de IPS)

**Asignatura:** Sistemas Distribuidos  
**Institución:** Universidad Antonio José de Sucre (UAJS)  
**Docente:** Ing. Jaider Reyes Herazo  
**Equipo:** Equipo de Trabajo - Sistemas Distribuidos  
**Versión:** `v1.0-alpha` (Fase 1 completada)

---

## 📁 Estructura del Repositorio

El proyecto sigue rigurosamente el estándar exigido en la guía del parcial:

```
plataforma_interoperabilidad/
├── app/                  # Frontend Web con las 4 vistas (Paciente, Admisionista, Médico, Reporte HC)
├── db/                   # Esquemas SQL, catálogos e inicialización de los 3 nodos PostgreSQL / Citus
├── docs/                 # Documentación e informes de entrega según la Plantilla v7
│   └── fase1_informe_arquitectura_uml.md
├── fhir/                 # Configuraciones HAPI FHIR, esquemas de recursos y perfiles
├── hsb/                  # Health Service Bus (FastAPI, normalizador FHIR, colas, reintentos e idempotencia)
├── infra/                # Manifiestos de Docker Compose, scripts de orquestación y variables de entorno
└── tests/                # Casos de prueba de integración, fixtures (HL7, CSV) y scripts de validación
```

---

## 🏥 Escenario de la Plataforma

Red regional de tres IPS con sistemas legados heterogéneos y bases de datos relacionales independientes:
- **Sede 1 — Sincelejo:** Laboratorio clínico ambulatorio (emite mensajes HL7 v2 `ORU^R01`).
- **Sede 2 — Cartagena:** Urgencias y hospitalización (emite mensajes HL7 v2 `ADT^A01`).
- **Sede 3 — Corozal:** Consulta externa comunitaria (emite archivos planos legados en formato `CSV`).

---

## 👥 Usuarios de Prueba y Roles de Acceso (RBAC)

| Rol | Usuario de Prueba | Contraseña de Prueba | Permisos Clave |
| :--- | :--- | :--- | :--- |
| **Paciente** | `paciente1007` | `paciente123` | Ver su propia historia clínica unificada, descargar Bundle FHIR. |
| **Admisionista** | `admision_sincelejo` | `admision123` | Buscar paciente, detectar duplicados, abrir atención con triage. |
| **Médico** | `medico_ruiz` | `medico123` | Consulta clínica completa, registrar diagnósticos CIE-10, ordenar medicamentos y egreso. |
| **Auditor** | `auditor_calidad` | `auditor123` | Reporte unificado, verificar cadena de auditoría SHA-256, tablero de salud de nodos. |

---

## ⚡ Comandos Rápidos de Ejecución (Fase 2+)

Para levantar todo el ecosistema con un solo comando:
```bash
docker compose up --build -d
```

Verificación del estado de los contenedores:
```bash
docker compose ps
```

---

## 📚 Documentación de Entrega

- [Informe de Fase 1: Análisis, Modelado UML y Arquitectura](docs/fase1_informe_arquitectura_uml.md)
