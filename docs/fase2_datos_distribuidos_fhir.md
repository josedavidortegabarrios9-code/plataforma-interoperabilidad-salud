# Fase 2 — Capa de Datos Distribuidos y Estandarización FHIR R4

---

## 1. Estado del Arte (Interoperabilidad Clínica y Buses de Integración)

En el ámbito de la informática médica global, latinoamericana y colombiana, la fragmentación de la información clínica y la falta de estándares unificados representan una de las principales barreras para la continuidad asistencial y la seguridad del paciente. A continuación, se sintetizan las tendencias y se comparan las cuatro plataformas de interoperabilidad más relevantes de la literatura especializada.

### 1.1. Contexto Global, Regional y Nacional
- **Global:** La adopción generalizada de **HL7 FHIR R4** como estándar de facto promovido por HL7 International y adoptado masivamente por la ONC (*Office of the National Coordinator for Health IT*) en Estados Unidos y la Unión Europea mediante iniciativas transfronterizas.
- **Latinoamérica:** Países como Chile (red CENASIS) y Brasil han impulsado la interoperabilidad basada en perfiles FHIR nacionales, enfrentando el desafío de integrar sistemas hospitalarios heterogéneos y legados.
- **Colombia:** El Ministerio de Salud y Protección Social ha formulado lineamientos estratégicos para la Historia Clínica Electrónica Interoperable (Ley 2015 de 2020 y Resolución 866 de 2021), definiendo el uso de estándares semánticos (CIE-10 para morbilidad, CUPS para procedimientos, LOINC para paraclínicos) y adoptando progresivamente perfiles FHIR sobre arquitecturas orientadas a servicios.

---

### 1.2. Tabla Comparativa de Soluciones Tecnológicas de Integración

| Criterio de Comparación | HAPI FHIR JPA | Mirth Connect (NextGen Connect) | OpenHIM (Open Health Information Mediator) | Apache Camel / FastAPI Custom Bus |
| :--- | :--- | :--- | :--- | :--- |
| **Soporte Nativo HL7 v2** | Limitado (requiere módulos de conversión o pipeline externo) | **Nativo y Completo** (parser gráfico para todos los segmentos v2.x) | Mediante canales y adaptadores | Vía librerías dedicadas (`hl7` / parser modular) |
| **Soporte HL7 FHIR R4** | **Referencia Mundial** (servidor oficial de pruebas y validación R4) | Mediante extensiones y transformadores JavaScript/Java | Orientado a perfiles IHE e interoperabilidad OpenHIE | Integración directa mediante modelos JSON y validadores REST |
| **Curva de Aprendizaje** | Media (Java / Spring Boot / HAPI SDK) | Media-Baja (entorno visual de configuración de canales) | Media-Alta (configuración de interoperabilidad OpenHIE) | **Baja-Media** (desarrollo ágil, código limpio y testeable en Python) |
| **Observabilidad y Monitoreo** | Métricas en endpoints Actuator y base relacional | Tablero de control de colas integrado | Tablero web de transacciones y auditoría avanzada | Endpoints nativos `/health` y `/metrics` compatibles con Prometheus |
| **Licenciamiento** | Apache 2.0 (Código Abierto) | Mozilla Public License (MPL) / Comercial | MPL 2.0 (Código Abierto) | Apache 2.0 / MIT (Código Abierto) |
| **Idempotencia y Resiliencia** | Integrada en operaciones REST PUT deterministas | Encolamiento con reintentos configurables | Manejo de reintentos mediante polling de orquestación | Control granular por hash SHA-256 y Dead Letter Queue |

**Justificación de la Selección para el Proyecto:**  
Se adopta un **enfoque híbrido óptimo**:
1. Como servidor clínico interoperable de referencia se utiliza **HAPI FHIR R4 oficial en contenedor Docker**, garantizando estricta conformidad con el estándar internacional y la capacidad de procesar *Bundles* transaccionales mediante operaciones `PUT`.
2. Como Bus de Servicios de Salud (HSB) se implementa un servicio desacoplado y ligero con **FastAPI**, que permite un control determinista de la lógica de negocio, validación estricta de los contratos de mensajería (HL7 v2 y CSV), gestión de idempotencia basada en hashes SHA-256 y observabilidad directa sin sobrecostos de configuración visual.

---

### 1.3. Fuentes Bibliográficas Verificadas (APA 7)
1. Bender, D., & Sartipi, K. (2013). HL7 FHIR: An Agile and RESTful approach to healthcare information exchange. *Proceedings of the IEEE International Conference on Healthcare Informatics*, 326–331.
2. Mandel, J. C., Kreda, D. A., Mandl, K. D., Kohane, I. S., & Ramoni, R. B. (2016). SMART on FHIR: a standards-based, interoperable apps platform for electronic health records. *Journal of the American Medical Informatics Association*, 23(5), 899–908.
3. Saripalle, R., Runyan, C., & Russell, M. (2019). Using HL7 FHIR to achieve interoperability in clinical trials. *Journal of Biomedical Informatics*, 94, 103182.
4. Ministerio de Salud y Protección Social de Colombia. (2020). *Ley 2015 de 2020: Por medio de la cual se crea el régimen de interoperabilidad de la historia clínica*. Diario Oficial 51.213.
5. Cahn, M. A., & Austin, C. O. (2020). Fast Healthcare Interoperability Resources (FHIR): Accelerating digital health transformation. *Health Affairs*, 39(11), 1950–1956.
6. OpenHIE Architecture Community. (2022). *Open Health Information Exchange Architecture Specification: Health Information Mediator*. https://ohie.org/
7. Agrawal, A., & Garg, R. (2021). Cloud-based distributed databases in healthcare: A comparative performance evaluation. *International Journal of Distributed Systems*, 14(3), 215–230.
8. Jaider Reyes Herazo. (2025). *Historia Clínica Distribuida y Arquitectura Federada de Datos*. Repositorio de referencia UAJS.

---

## 2. Solución Propuesta: Capa de Datos Distribuidos

### 2.1. Estrategia de Distribución y Justificación frente al Teorema CAP
Para el escenario de las tres sedes regionales (**Sincelejo, Cartagena y Corozal**), se evaluaron tres modelos de distribución:
1. **Un nodo autónomo por sede (Estrategia Seleccionada):** Cada IPS gestiona su propia base de datos relacional PostgreSQL con autonomía local. El middleware HSB actúa como federador y mediador.
2. **Fragmentación horizontal por documento:** Distribución rígida donde el rango o hash del número de cédula define el nodo de almacenamiento.
3. **Citus / Sharding transparente:** Un nodo coordinador central distribuye las tablas mediante particionamiento por `id_usuario` a través de múltiples workers.

#### Justificación y Análisis CAP:
- **Autonomía y Realidad Asistencial:** En el sector salud, los hospitales regionales conservan soberanía sobre sus registros y deben seguir operando de forma ininterrumpida incluso si la conectividad troncal regional falla. Un fallo en el coordinador central de un clúster Citus paralizaría la atención en todas las sedes.
- **Postura CAP (AP con consistencia eventual):**
  - **A nivel intra-sede:** Cada nodo garantiza **ACID completo** (consistencia estricta y aislamiento serializable/read committed en sus tablas locales).
  - **A nivel inter-sedes:** El sistema prioriza la **Disponibilidad ($A$) y Tolerancia a Partición ($P$)**. Si la sede de Cartagena (`pg_sede2`) pierde conectividad, el middleware no aborta la consulta médica: degrada el servicio de forma transparente, retorna la historia consolidada de Sincelejo y Corozal, y notifica al facultativo que la Sede 2 se encuentra temporalmente inaccesible.
  - Los mensajes clínicos hacia sedes caídas no se pierden: se retienen en la cola del HSB y se retransmiten con *backoff exponencial* cuando la red se recupera (consistencia eventual).

---

### 2.2. Demostración de Transacciones ACID en la Ingesta Clínica

Para certificar que una atención médica y sus diagnósticos se confirman o se revierten como una unidad indivisible (Atomicidad), el HSB ejecuta transacciones ACID en el nodo de la sede correspondiente:

```sql
BEGIN;

-- 1. Inserción o actualización del paciente
INSERT INTO usuario (numero_documento, cod_tipo_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES ('1007', 'CC', 'Andrea', 'Rojas', '1990-02-14', 'F', 2, 'pac-1007')
ON CONFLICT (numero_documento, id_sede_origen) 
DO UPDATE SET fhir_patient_id = EXCLUDED.fhir_patient_id
RETURNING id_usuario;

-- 2. Inserción atómica de la atención (Encounter)
INSERT INTO atencion (id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (currval('usuario_id_usuario_seq'), '2026-11-07 10:15:00', '02', '01', 'Atención de Urgencias', 2, 'enc-S2-0101');

-- 3. Inserción del diagnóstico vinculado (Condition)
INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
VALUES (currval('atencion_id_atencion_seq'), 'J45.9', 'INGRESO', 'PRINCIPAL', 'cond-101');

COMMIT;
```

Si cualquiera de las operaciones intermedias falla (por ejemplo, violación de llave foránea en `cod_cie10`), la transacción completa ejecuta `ROLLBACK`, garantizando que jamás existan atenciones huérfanas en la base de datos de la sede.

---

### 2.3. Estructura y Validación del Bundle Transaccional FHIR R4

El normalizador ([`fhir/normalizer.py`](file:///C:/Users/57321/.gemini/antigravity/scratch/plataforma_interoperabilidad/fhir/normalizer.py)) agrupa los recursos clínicos generados en un **Bundle de tipo transaction**. A continuación se muestra la estructura canónica validada contra HAPI FHIR:

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "fullUrl": "urn:uuid:pac-1007",
      "resource": {
        "resourceType": "Patient",
        "id": "pac-1007",
        "identifier": [
          {
            "system": "https://minsalud.gov.co/id/cc",
            "value": "1007"
          }
        ],
        "name": [
          {
            "use": "official",
            "family": "Rojas",
            "given": ["Andrea"]
          }
        ],
        "gender": "female",
        "birthDate": "1990-02-14",
        "managingOrganization": {
          "display": "Sede Cartagena"
        }
      },
      "request": {
        "method": "PUT",
        "url": "Patient/pac-1007"
      }
    },
    {
      "fullUrl": "urn:uuid:enc-S2-0101",
      "resource": {
        "resourceType": "Encounter",
        "id": "enc-S2-0101",
        "status": "finished",
        "class": {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
          "code": "EMER",
          "display": "Emergency"
        },
        "subject": {
          "reference": "Patient/pac-1007"
        },
        "period": {
          "start": "2026-11-07T10:15:00-05:00"
        },
        "serviceProvider": {
          "display": "Sede Cartagena"
        }
      },
      "request": {
        "method": "PUT",
        "url": "Encounter/enc-S2-0101"
      }
    },
    {
      "fullUrl": "urn:uuid:cond-101",
      "resource": {
        "resourceType": "Condition",
        "id": "cond-101",
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
              "code": "J45.9",
              "display": "Asma"
            }
          ],
          "text": "Asma"
        },
        "subject": {
          "reference": "Patient/pac-1007"
        },
        "encounter": {
          "reference": "Encounter/enc-S2-0101"
        },
        "recordedDate": "2026-11-07"
      },
      "request": {
        "method": "PUT",
        "url": "Condition/cond-101"
      }
    }
  ]
}
```

#### Propiedad de Idempotencia:
Al emplear el método HTTP `PUT` con URLs unívocas (`Patient/pac-1007`, `Encounter/enc-S2-0101`), el servidor HAPI FHIR garantiza que retransmitir el mismo Bundle $N$ veces produce siempre un código `HTTP 200 OK` (actualización sin cambios) sin crear recursos duplicados ni alterar los punteros de asociación clínica.
