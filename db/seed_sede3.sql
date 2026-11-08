-- Seed Sede 3 (Corozal)
\i /docker-entrypoint-initdb.d/init_schema.sql
\i /docker-entrypoint-initdb.d/catalogs.sql

INSERT INTO profesional_salud (id_profesional, cod_tipo_documento, numero_documento, nombre_completo, registro_medico, id_sede) VALUES
(3, 'CC', '503003', 'Dra. Andrea Soler', 'RM-7021', 3)
ON CONFLICT DO NOTHING;

-- Paciente 1001 (Multi-sede)
INSERT INTO usuario (id_usuario, cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES (1, 'CC', '1001', 'Carlos', 'Perez', '1980-04-12', 'M', 3, NULL)
ON CONFLICT DO NOTHING;

-- Paciente 1004 (Local Sede 3)
INSERT INTO usuario (id_usuario, cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES (4, 'CC', '1004', 'Luisa', 'Ramirez', '2000-11-05', 'F', 3, NULL)
ON CONFLICT DO NOTHING;

-- Atenciones
INSERT INTO atencion (id_atencion, id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (201, 1, '2026-11-03 10:15:00', '01', '01', 'Seguimiento endocrinológico', 3, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
VALUES (201, 'E11.9', 'INGRESO', 'PRINCIPAL', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO atencion (id_atencion, id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (202, 4, '2026-11-02 08:00:00', '02', '01', 'Dificultad respiratoria y fiebre', 3, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO triage (id_atencion, fecha_hora_triage, cod_triage, observaciones)
VALUES (202, '2026-11-02 08:05:00', '2', 'Disnea y tiraje intercostal')
ON CONFLICT DO NOTHING;

INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
VALUES (202, 'J18.9', 'INGRESO', 'PRINCIPAL', NULL)
ON CONFLICT DO NOTHING;
