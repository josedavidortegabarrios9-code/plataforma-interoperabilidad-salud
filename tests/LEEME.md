# Mensajes de ejemplo para el HSB

Estos archivos son el **contrato** que debe cumplir su HSB (Fase 3). No los modifique: su sistema debe producir los resultados de la tabla.

| Archivo | Formato | Resultado esperado |
| --- | --- | --- |
| 01_adt_a01_valido_sede2.hl7 | HL7 v2 ADT^A01 | Entregado: Patient 1007, Encounter y Condition J45.9 en la sede 2 |
| 02_oru_r01_laboratorio_sede1.hl7 | HL7 v2 ORU^R01 | Entregado: Observation LOINC 718-7 = 13,8 g/dL para el paciente 1001 en la sede 1 |
| 03_adt_a01_invalido.hl7 | HL7 v2 ADT^A01 | Rechazado con 3 motivos: documento no numérico, sexo no válido, diagnóstico sin mapeo a CIE-10 |
| 04_sede3_legado.csv | CSV legado (separador `;`) | 3 entregados (1008, 1009, 1010) y 2 rechazados (dx sin mapeo; documento de 2 dígitos) |
| 05_ref_terminologia.csv | Tabla de referencia | Diagnóstico local → CIE-10 que usa el normalizador |

Pruebas adicionales que debe hacer:

1. Reenviar `01_adt_a01_valido_sede2.hl7` dos veces: la segunda vez el bus responde `duplicado` y no se crea otro paciente.
2. Apagar HAPI mientras se envía `02`: el mensaje pasa a `reintentando` y termina `entregado` cuando HAPI vuelve.
3. Dejar HAPI apagado más intentos que el máximo: el mensaje queda en `muerto` (cola de mensajes muertos).

Los datos son sintéticos. Está prohibido usar datos reales de pacientes.
