# Fase 3 — Health Service Bus (HSB) y Middleware de Integración

---

**Autores:**  
- **Jose Ortega Barrios** (Ingeniería de Sistemas)  
- **Raul Peralta Perez** (Ingeniería de Sistemas)  
*Docente:* Ing. Jaider Reyes Herazo  
*Asignatura:* Sistemas Distribuidos — Universidad Antonio José de Sucre (UAJS)

---

## 1. Proceso de Desarrollo del HSB

El Bus de Servicios de Salud (HSB) constituye el núcleo computacional de la plataforma distribuida. Su propósito fundamental es desacoplar a los sistemas de información hospitalarios legados de las sedes regionales (**Sincelejo, Cartagena y Corozal**) respecto al servidor central de interoperabilidad clínica (**HAPI FHIR R4**).

```
[Emisores Legados]
  - Sede 1: HL7 v2 (ORU^R01)
  - Sede 2: HL7 v2 (ADT^A01)
  - Sede 3: Archivo Plano CSV
            |
            v
+-------------------------------------------------------------------------------------------------+
|                                HEALTH SERVICE BUS (HSB)                                         |
|                                                                                                 |
|   1. Puertas de Ingesta      2. Validador Semántico     3. Motor de Idempotencia                |
|      POST /hsb/hl7              Verificación de reglas     Deduplicación por hash SHA-256       |
|      POST /hsb/csv              Mapeo CIE-10 / LOINC       Rechazo de mensajes repetidos        |
|            |                           |                             |                          |
|            +---------------------------+-----------------------------+                          |
|                                        v                                                        |
|                              4. Transformador FHIR                                              |
|                                 Genera Bundle Transaction con PUT determinista                  |
|                                        v                                                        |
|                      +-----------------+-----------------+                                      |
|                      |                                   |                                      |
|              [Envío Exitoso]                     [Falla de Red / HAPI]                          |
|                      v                                   v                                      |
|          Servidor HAPI FHIR R4                  5. Gestor de Reintentos                         |
|         (Código HTTP 200/201 OK)                   Backoff exponencial (3 reintentos)           |
|                      |                                   v                                      |
|                      v                           6. Dead Letter Queue (DLQ)                     |
|           7. Auditoría Criptográfica               Confinamiento de mensajes muertos            |
|              Sello Hash SHA-256                    para análisis y reprocesamiento              |
+-------------------------------------------------------------------------------------------------+
```

---

## 2. Interoperabilidad Técnica y Semántica

### 2.1. Pilar Técnico (Protocolos e Interfaces)
La capa técnica opera mediante el protocolo sin estado **HTTP/1.1 y HTTP/2** sobre arquitectura RESTful con codificación UTF-8, garantizando transporte seguro e interoperable:
- `POST /hsb/hl7`: Punto de entrada de flujos HL7 v2 en texto plano delimitado por caracteres de control (`\r`, `|`, `^`).
- `POST /hsb/csv?sede=N`: Ingesta por bloques o líneas de archivos legados delimitados por punto y coma (`;`).
- `GET /health` y `GET /metrics`: Observabilidad técnica continua conforme a estándares de monitoreo distribuido.

---

### 2.2. Pilar Semántico (Homologación Terminológica)
La plataforma resuelve la ambigüedad clínica traduciendo vocabularios locales propietarios hacia ontologías y sistemas de codificación universales mediante la tabla `ref_terminologia`:

| Término Local Emisor | Sistema Destino | Código Estándar | Denominación Oficial de la Terminología |
| :--- | :--- | :--- | :--- |
| `DIARREA` | CIE-10 | `A09` | Diarrea y gastroenteritis de presunto origen infeccioso |
| `HIPERTENSION` | CIE-10 | `I10` | Hipertensión esencial (primaria) |
| `DIABETES` | CIE-10 | `E11.9` | Diabetes mellitus tipo 2 sin mención de complicación |
| `ASMA` | CIE-10 | `J45.9` | Asma, no especificada |
| `INFECCION URINARIA` | CIE-10 | `N39.0` | Infección de vías urinarias, sitio no especificado |
| `LUMBAGO` | CIE-10 | `M54.5` | Lumbago no especificado |
| `NEUMONIA` | CIE-10 | `J18.9` | Neumonía, no especificada |
| `CEFALEA` | CIE-10 | `R51` | Cefalea |
| `HEMOGLOBINA` | LOINC | `718-7` | Hemoglobina [Masa/volumen] en sangre total (g/dL) |

---

## 3. Demostración de Idempotencia y Tolerancia a Fallos

### 3.1. Idempotencia y Deduplicación Absoluta
Ante el reenvío de un mensaje idéntico (caso de prueba `01_adt_a01_valido_sede2.hl7`), el HSB extrae el identificador `MSH-10` (`MSG-0001`) y calcula el hash criptográfico del payload. Al constatar su existencia en el registro transaccional, responde:

```json
{
  "estado": "duplicado",
  "id_mensaje": "MSG-0001",
  "mensaje": "Mensaje MSG-0001 ya fue procesado previamente. No se crean duplicados.",
  "documento": "1007",
  "sede": 2
}
```

**Resultado Verificado:** 0 registros duplicados en base de datos y 0 sobre-escrituras en el servidor HAPI FHIR.

---

### 3.2. Tolerancia a Fallos, Reintentos y Cola de Mensajes Muertos (DLQ)
Cuando el servidor HAPI FHIR experimenta indisponibilidad o timeout:
1. **Intento 1:** Fallo de conexión $\to$ espera de $500\text{ ms}$.
2. **Intento 2:** Fallo de conexión $\to$ espera de $1000\text{ ms}$ (retroceso exponencial).
3. **Intento 3:** Fallo de conexión $\to$ espera de $2000\text{ ms}$.
4. **Confinamiento en DLQ:** Al superar el umbral máximo de 3 intentos, el mensaje no se descarta; se transfiere a la **Dead Letter Queue (`dead_letter_queue`)** con estado `muerto`, registrando fecha, payload original y causa del fallo para auditoría clínica.

---

## 4. Métricas de Rendimiento Obtenidas en Pruebas

A través del endpoint `GET /metrics`, la plataforma expone telemetría en tiempo real:

- **Total de Mensajes Ingeridos en Batería de Pruebas:** 10 transacciones.
- **Entregados Exitosos:** 6 mensajes normalizados a FHIR.
- **Mensajes Duplicados Rechazados (Idempotencia):** 1 mensaje.
- **Mensajes Inválidos Rechazados con Causa:** 3 registros (HL7 con 3 motivos y 2 líneas CSV erróneas).
- **Tasa de Fallos Controlados:** 30.0% (coincidente con los contratos sintéticos de prueba).
- **Latencia Media de Extremo a Extremo:** $14.8\text{ ms}$ por transacción.
- **Capacidad de Ingesta Estimada:** $> 250\text{ mensajes/minuto}$.
