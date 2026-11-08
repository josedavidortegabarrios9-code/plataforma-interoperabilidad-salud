-- Seed Sede 2 (Cartagena)
\i /docker-entrypoint-initdb.d/init_schema.sql
\i /docker-entrypoint-initdb.d/catalogs.sql

INSERT INTO profesional_salud (id_profesional, cod_tipo_documento, numero_documento, nombre_completo, registro_medico, id_sede) VALUES
(2, 'CC', '502002', 'Dr. Mateo Ruiz', 'RM-1301', 2)
ON CONFLICT DO NOTHING;

-- Paciente 1001 (Multi-sede)
INSERT INTO usuario (id_usuario, cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES (1, 'CC', '1001', 'Carlos', 'Perez', '1980-04-12', 'M', 2, NULL)
ON CONFLICT DO NOTHING;

-- Paciente 1003 (Local Sede 2)
INSERT INTO usuario (id_usuario, cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES (3, 'CC', '1003', 'Juan', 'Morales', '1992-09-14', 'M', 2, NULL)
ON CONFLICT DO NOTHING;

-- Atenciones
INSERT INTO atencion (id_atencion, id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (101, 1, '2026-11-05 16:45:00', '02', '01', 'Urgencias por cefalea intensa', 2, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO triage (id_atencion, fecha_hora_triage, cod_triage, observaciones)
VALUES (101, '2026-11-05 16:50:00', '3', 'Dolor pulsátil escala 7/10')
ON CONFLICT DO NOTHING;

INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
VALUES (101, 'R51', 'INGRESO', 'PRINCIPAL', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO egreso (id_atencion, fecha_hora_salida, cod_condicion_salida, id_profesional_responsable, sello_integridad)
VALUES (101, '2026-11-05 20:00:00', '01', 2, 'SELLO-CARTAGENA-101')
ON CONFLICT DO NOTHING;

INSERT INTO atencion (id_atencion, id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (102, 3, '2026-11-04 14:10:00', '01', '02', 'Dolor lumbar agudo', 2, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
VALUES (102, 'M54.5', 'INGRESO', 'PRINCIPAL', NULL)
ON CONFLICT DO NOTHING;
