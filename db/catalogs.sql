-- Carga de Catálogos y Terminologías
INSERT INTO cat_tipo_documento (cod_tipo_documento, nombre) VALUES
('CC', 'Cédula de Ciudadanía'),
('TI', 'Tarjeta de Identidad'),
('RC', 'Registro Civil'),
('CE', 'Cédula de Extranjería')
ON CONFLICT DO NOTHING;

INSERT INTO cat_sexo (cod_sexo, nombre) VALUES
('M', 'Masculino'),
('F', 'Femenino'),
('O', 'Otro')
ON CONFLICT DO NOTHING;

INSERT INTO cat_cie10 (cod_cie10, descripcion) VALUES
('A09', 'Diarrea y gastroenteritis de presunto origen infeccioso'),
('I10', 'Hipertensión esencial (primaria)'),
('E11.9', 'Diabetes mellitus tipo 2 sin mención de complicación'),
('J45.9', 'Asma, no especificada'),
('N39.0', 'Infección de vías urinarias, sitio no especificado'),
('M54.5', 'Lumbago no especificado'),
('J18.9', 'Neumonía, no especificada'),
('R51', 'Cefalea')
ON CONFLICT DO NOTHING;

INSERT INTO ref_terminologia (cod_local, sistema_destino, cod_estandar, descripcion_estandar) VALUES
('DIARREA', 'CIE-10', 'A09', 'Diarrea y gastroenteritis'),
('HIPERTENSION', 'CIE-10', 'I10', 'Hipertensión esencial'),
('DIABETES', 'CIE-10', 'E11.9', 'Diabetes mellitus tipo 2'),
('ASMA', 'CIE-10', 'J45.9', 'Asma'),
('INFECCION URINARIA', 'CIE-10', 'N39.0', 'Infección de vías urinarias'),
('LUMBAGO', 'CIE-10', 'M54.5', 'Lumbago'),
('NEUMONIA', 'CIE-10', 'J18.9', 'Neumonía'),
('CEFALEA', 'CIE-10', 'R51', 'Cefalea'),
('HEMOGLOBINA', 'LOINC', '718-7', 'Hemoglobina [Masa/volumen] en sangre')
ON CONFLICT DO NOTHING;

-- Sedes Oficiales
INSERT INTO sede (id_sede, nombre_ciudad, codigo_prestador) VALUES
(1, 'Sincelejo', '700010000101'),
(2, 'Cartagena', '130010000201'),
(3, 'Corozal', '702150000301')
ON CONFLICT DO NOTHING;
