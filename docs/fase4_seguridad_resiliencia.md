# Fase 4 — Seguridad, Confianza Criptográfica y Resiliencia Distribuida

---

**Autores:**  
- **Jose Ortega Barrios** (Ingeniería de Sistemas)  
- **Raul Peralta Perez** (Ingeniería de Sistemas)  
*Docente:* Ing. Jaider Reyes Herazo  
*Asignatura:* Sistemas Distribuidos — Universidad Antonio José de Sucre (UAJS)

---

## 1. Seguridad y Control de Acceso Basado en Roles (RBAC)

Para garantizar la confidencialidad de la historia clínica digital y la mínima exposición de datos sensibles, la plataforma implementa **Control de Acceso Basado en Roles (RBAC)** con validación de tokens en cada invocación:

| Rol | Identidad de Prueba | Acceso Permitido | Restricción Estricta (Acceso Denegado HTTP 403) |
| :--- | :--- | :--- | :--- |
| **Paciente** | `paciente1001` | Consultar su propia historia unificada, descargar su Bundle FHIR y ver la bitácora de quién accedió a sus datos. | Modificar historias clínicas o consultar registros de otros pacientes. |
| **Admisionista** | `admision_sincelejo` | Buscar pacientes, detectar duplicados inter-sedes y abrir atenciones con nivel de triage. | **Ver diagnósticos clínicos**, notas médicas o prescripciones farmacológicas. |
| **Médico** | `medico_ruiz` | Consultar historia unificada completa, registrar diagnósticos CIE-10, ordenar tecnologías en salud y asentar egresos. | Alterar eventos de auditoría o usurpar la identidad de otros facultativos. |
| **Auditor** | `auditor_calidad` | Acceso al reporte unificado de calidad, tablero de salud de nodos y verificación de integridad criptográfica. | Modificar o insertar registros clínicos asistenciales. |

---

## 2. Auditoría Criptográfica Encadenada (Tamper-Evident Ledger)

Cada acción sobre la plataforma (ingesta de mensaje, consulta de historia clínica, conmutación de nodo, etc.) genera un evento de auditoría conforme al recurso `AuditEvent` de FHIR. Para impedir la manipulación o el borrado no detectado de registros de acceso, los eventos se encadenan mediante una función de dispersión unidireccional **SHA-256**:

$$H_n = \text{SHA-256}(\text{Timestamp} \parallel \text{Actor} \parallel \text{Rol} \parallel \text{Acción} \parallel \text{Recurso} \parallel \text{Resultado} \parallel H_{n-1})$$

Donde $H_0$ corresponde al hash génesis de inicialización del sistema.

### 2.1. Algoritmo Verificador de Integridad
El endpoint `GET /audit/verify` ejecuta una validación secuencial:
1. Comprueba que el puntero `hash_previo` del evento $n$ sea idéntico al `hash_actual` del evento $n-1$.
2. Recalcula el hash del payload del evento $n$ y lo compara con el `hash_actual` almacenado.

**Prueba de Alteración Maliciosa Demostrada en Pruebas Unitarias (`test_08`):**  
Al invocar `POST /audit/tamper?evento_id=1`, se modifica un carácter en la base de datos de auditoría. De inmediato, el verificador reporta:

```json
{
  "integro": false,
  "evento_alterado_id": 1,
  "indice": 0,
  "motivo": "Contenido modificado en evento 1: el hash actual no coincide con los datos sellados"
}
```

---

## 3. Resiliencia y Tolerancia a Fallos Parciales

En cumplimiento del Teorema CAP (orientación AP con degradación elegante), la plataforma soporta la desconexión total o temporal de cualquiera de los nodos hospitalarios:

```
[Cliente / Frontend]
         |
         | Consulta Unificada (Paciente CC 1001)
         v
[Health Service Bus]
   |---> Nodo Sede 1 (Sincelejo): [OPERATIVO] -> Retorna Hemoglobina (LOINC 718-7)
   |---> Nodo Sede 2 (Cartagena): [CAÍDO / TIMEOUT] -> Timeout capturado (1.5s)
   |---> Nodo Sede 3 (Corozal):   [OPERATIVO] -> Retorna Diabetes (CIE-10 E11.9)
         |
         v
[Respuesta Unificada con Degradación Elegante - HTTP 200 OK]
  - Total Atenciones Devueltas: 2
  - Sedes Activas: Sede 1 y Sede 3
  - Sedes Inactivas Reportadas: ["Sede 2: Cartagena (CAÍDA_NO_DISPONIBLE)"]
  - Flag Resiliencia: "degradacion_tolerante": true
```

La interfaz web médica activa inmediatamente una alerta visual en amarillo informando al médico que la Sede 2 se encuentra temporalmente fuera de línea, pero **el sistema no se bloquea ni genera error 500**.

---

## 4. Viabilidad Técnica y Cumplimiento Normativo

- **Escalabilidad Horizontal:** La capa de mediación (HSB) no almacena estado de sesión (*stateless* con tokens JWT), lo que permite instanciar $N$ réplicas del contenedor detrás de un balanceador de carga (HAProxy o Nginx).
- **Cumplimiento Legal (Ley 1581 de 2012 - Colombia):** La plataforma garantiza el principio de finalidad y seguridad en el tratamiento de datos de salud sensibles mediante cifrado y auditoría inmutable de accesos.
