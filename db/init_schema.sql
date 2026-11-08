-- Esquema Unificado de Base de Datos para cada Sede Legada
-- Sede 1: Sincelejo | Sede 2: Cartagena | Sede 3: Corozal

CREATE TABLE IF NOT EXISTS sede (
    id_sede SERIAL PRIMARY KEY,
    nombre_ciudad VARCHAR(60) NOT NULL,
    codigo_prestador VARCHAR(12) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_cie10 (
    cod_cie10 VARCHAR(8) PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_tipo_documento (
    cod_tipo_documento VARCHAR(2) PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_sexo (
    cod_sexo VARCHAR(1) PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS profesional_salud (
    id_profesional SERIAL PRIMARY KEY,
    cod_tipo_documento VARCHAR(2) NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    registro_medico VARCHAR(30),
    id_sede INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario SERIAL PRIMARY KEY,
    cod_tipo_documento VARCHAR(2) NOT NULL DEFAULT 'CC',
    numero_documento VARCHAR(20) NOT NULL,
    primer_nombre VARCHAR(50) NOT NULL,
    segundo_nombre VARCHAR(50),
    primer_apellido VARCHAR(50) NOT NULL,
    segundo_apellido VARCHAR(50),
    fecha_nacimiento DATE NOT NULL,
    cod_sexo VARCHAR(1) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(120),
    id_sede_origen INTEGER NOT NULL,
    fhir_patient_id VARCHAR(64),
    CONSTRAINT usuario_doc_sede_unique UNIQUE (numero_documento, id_sede_origen)
);

CREATE TABLE IF NOT EXISTS atencion (
    id_atencion SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    fecha_hora_ingreso TIMESTAMP NOT NULL,
    cod_modalidad VARCHAR(2) NOT NULL DEFAULT '01',
    cod_via_ingreso VARCHAR(2) NOT NULL DEFAULT '01',
    causa_atencion TEXT NOT NULL,
    id_profesional INTEGER REFERENCES profesional_salud(id_profesional),
    fhir_encounter_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS triage (
    id_atencion INTEGER PRIMARY KEY REFERENCES atencion(id_atencion) ON DELETE CASCADE,
    fecha_hora_triage TIMESTAMP NOT NULL,
    cod_triage VARCHAR(3) NOT NULL,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS diagnostico (
    id_diagnostico SERIAL PRIMARY KEY,
    id_atencion INTEGER NOT NULL REFERENCES atencion(id_atencion) ON DELETE CASCADE,
    cod_cie10 VARCHAR(8) NOT NULL,
    momento VARCHAR(10) NOT NULL DEFAULT 'INGRESO',
    tipo VARCHAR(12) NOT NULL DEFAULT 'PRINCIPAL',
    fhir_condition_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS tecnologia_salud (
    id_tecnologia SERIAL PRIMARY KEY,
    id_atencion INTEGER NOT NULL REFERENCES atencion(id_atencion) ON DELETE CASCADE,
    id_profesional INTEGER REFERENCES profesional_salud(id_profesional),
    descripcion_tecnologia VARCHAR(200) NOT NULL,
    codigo_loinc VARCHAR(20),
    resultado_valor NUMERIC(10,2),
    unidad_medida VARCHAR(20),
    dias_tratamiento INTEGER,
    fhir_observation_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS egreso (
    id_atencion INTEGER PRIMARY KEY REFERENCES atencion(id_atencion) ON DELETE CASCADE,
    fecha_hora_salida TIMESTAMP NOT NULL,
    cod_condicion_salida VARCHAR(2) NOT NULL DEFAULT '01',
    id_profesional_responsable INTEGER REFERENCES profesional_salud(id_profesional),
    sello_integridad VARCHAR(64)
);

-- Tablas de infraestructura de integración y auditoría local
CREATE TABLE IF NOT EXISTS ref_terminologia (
    cod_local VARCHAR(50) PRIMARY KEY,
    sistema_destino VARCHAR(20) NOT NULL,
    cod_estandar VARCHAR(20) NOT NULL,
    descripcion_estandar VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS evento_auditoria (
    id_evento SERIAL PRIMARY KEY,
    fecha_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor_username VARCHAR(50) NOT NULL,
    rol_actor VARCHAR(30) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    recurso_afectado VARCHAR(100) NOT NULL,
    resultado VARCHAR(20) NOT NULL,
    hash_previo VARCHAR(64) NOT NULL,
    hash_actual VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS mensaje_bus (
    id_mensaje VARCHAR(64) PRIMARY KEY,
    formato_origen VARCHAR(20) NOT NULL,
    id_sede_origen INTEGER NOT NULL,
    hash_contenido VARCHAR(64) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    intentos INTEGER DEFAULT 1,
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload_raw TEXT NOT NULL,
    payload_fhir JSONB
);
