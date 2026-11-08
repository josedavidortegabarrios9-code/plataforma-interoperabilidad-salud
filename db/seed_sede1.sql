-- Seed Sede 1 (Sincelejo)

INSERT INTO profesional_salud (id_profesional, cod_tipo_documento, numero_documento, nombre_completo, registro_medico, id_sede) VALUES
(1, 'CC', '501001', 'Dra. Laura Vega', 'RM-7001', 1)
ON CONFLICT DO NOTHING;

-- Paciente 1001 (Multi-sede)
INSERT INTO usuario (id_usuario, cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES (1, 'CC', '1001', 'Carlos', 'Perez', '1980-04-12', 'M', 1, NULL)
ON CONFLICT DO NOTHING;

-- Paciente 1002 (Local Sede 1)
INSERT INTO usuario (id_usuario, cod_tipo_documento, numero_documento, primer_nombre, primer_apellido, fecha_nacimiento, cod_sexo, id_sede_origen, fhir_patient_id)
VALUES (2, 'CC', '1002', 'Maria', 'Gonzalez', '1985-06-20', 'F', 1, NULL)
ON CONFLICT DO NOTHING;

-- Atenciones
INSERT INTO atencion (id_atencion, id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (1, 1, '2026-11-07 11:00:00', '01', '01', 'Evaluación de laboratorio clínico', 1, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO tecnologia_salud (id_atencion, id_profesional, descripcion_tecnologia, codigo_loinc, resultado_valor, unidad_medida, fhir_observation_id)
VALUES (1, 1, 'Hemoglobina en sangre', '718-7', 13.80, 'g/dL', NULL)
ON CONFLICT DO NOTHING;

INSERT INTO atencion (id_atencion, id_usuario, fecha_hora_ingreso, cod_modalidad, cod_via_ingreso, causa_atencion, id_profesional, fhir_encounter_id)
VALUES (2, 2, '2026-11-06 09:30:00', '01', '02', 'Control ambulatorio', 1, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO diagnostico (id_atencion, cod_cie10, momento, tipo, fhir_condition_id)
VALUES (2, 'I10', 'INGRESO', 'PRINCIPAL', NULL)
ON CONFLICT DO NOTHING;
