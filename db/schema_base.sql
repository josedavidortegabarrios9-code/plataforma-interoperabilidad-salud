CREATE TABLE IF NOT EXISTS "sede" (
	"id_sede" SERIAL,
	"nombre_ciudad" VARCHAR(60) NOT NULL,
	PRIMARY KEY("id_sede")
);

CREATE TABLE IF NOT EXISTS "cat_tipo_documento" (
	"cod_tipo_documento" VARCHAR(2),
	"nombre" VARCHAR(60) NOT NULL,
	PRIMARY KEY("cod_tipo_documento")
);

CREATE TABLE IF NOT EXISTS "cat_pais" (
	"cod_pais" VARCHAR(3),
	"nombre" VARCHAR(80) NOT NULL,
	PRIMARY KEY("cod_pais")
);

CREATE TABLE IF NOT EXISTS "cat_departamento" (
	"cod_departamento" VARCHAR(2),
	"nombre" VARCHAR(80) NOT NULL,
	PRIMARY KEY("cod_departamento")
);

CREATE TABLE IF NOT EXISTS "cat_municipio" (
	"cod_municipio" VARCHAR(5),
	"nombre" VARCHAR(80) NOT NULL,
	"cod_departamento" VARCHAR(2) NOT NULL,
	PRIMARY KEY("cod_municipio")
);

CREATE TABLE IF NOT EXISTS "cat_sexo" (
	"cod_sexo" VARCHAR(1),
	"nombre" VARCHAR(30) NOT NULL,
	PRIMARY KEY("cod_sexo")
);

CREATE TABLE IF NOT EXISTS "cat_genero" (
	"cod_genero" VARCHAR(2),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_genero")
);

CREATE TABLE IF NOT EXISTS "cat_ocupacion" (
	"cod_ocupacion" VARCHAR(10),
	"nombre" VARCHAR(120) NOT NULL,
	PRIMARY KEY("cod_ocupacion")
);

CREATE TABLE IF NOT EXISTS "cat_discapacidad" (
	"cod_discapacidad" VARCHAR(2),
	"nombre" VARCHAR(60) NOT NULL,
	PRIMARY KEY("cod_discapacidad")
);

CREATE TABLE IF NOT EXISTS "cat_etnia" (
	"cod_etnia" VARCHAR(2),
	"nombre" VARCHAR(60) NOT NULL,
	PRIMARY KEY("cod_etnia")
);

CREATE TABLE IF NOT EXISTS "cat_comunidad_etnica" (
	"id_comunidad_etnica" SERIAL,
	"nombre" VARCHAR(80) NOT NULL,
	"cod_etnia" VARCHAR(2) NOT NULL,
	PRIMARY KEY("id_comunidad_etnica")
);

CREATE TABLE IF NOT EXISTS "cat_zona" (
	"cod_zona" VARCHAR(1),
	"nombre" VARCHAR(20) NOT NULL,
	PRIMARY KEY("cod_zona")
);

CREATE TABLE IF NOT EXISTS "cat_parentesco" (
	"cod_parentesco" VARCHAR(2),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_parentesco")
);

CREATE TABLE IF NOT EXISTS "cat_entidad_salud" (
	"cod_entidad" VARCHAR(10),
	"nombre" VARCHAR(120) NOT NULL,
	PRIMARY KEY("cod_entidad")
);

CREATE TABLE IF NOT EXISTS "cat_modalidad" (
	"cod_modalidad" VARCHAR(2),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_modalidad")
);

CREATE TABLE IF NOT EXISTS "cat_entorno" (
	"cod_entorno" VARCHAR(2),
	"nombre" VARCHAR(60) NOT NULL,
	PRIMARY KEY("cod_entorno")
);

CREATE TABLE IF NOT EXISTS "cat_via_ingreso" (
	"cod_via_ingreso" VARCHAR(2),
	"nombre" VARCHAR(60) NOT NULL,
	PRIMARY KEY("cod_via_ingreso")
);

CREATE TABLE IF NOT EXISTS "cat_clasificacion_triage" (
	"cod_triage" VARCHAR(3),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_triage")
);

CREATE TABLE IF NOT EXISTS "cat_cie10" (
	"cod_cie10" VARCHAR(8),
	"descripcion" VARCHAR(255) NOT NULL,
	PRIMARY KEY("cod_cie10")
);

CREATE TABLE IF NOT EXISTS "cat_medicamento" (
	"id_medicamento" SERIAL,
	"nombre" VARCHAR(150) NOT NULL,
	PRIMARY KEY("id_medicamento")
);

CREATE TABLE IF NOT EXISTS "cat_unidad_medida" (
	"cod_unidad_medida" VARCHAR(10),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_unidad_medida")
);

CREATE TABLE IF NOT EXISTS "cat_via_administracion" (
	"cod_via_admin" VARCHAR(3),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_via_admin")
);

CREATE TABLE IF NOT EXISTS "cat_unidad_tiempo" (
	"cod_unidad_tiempo" VARCHAR(3),
	"nombre" VARCHAR(20) NOT NULL,
	PRIMARY KEY("cod_unidad_tiempo")
);

CREATE TABLE IF NOT EXISTS "cat_finalidad" (
	"cod_finalidad" VARCHAR(2),
	"nombre" VARCHAR(40) NOT NULL,
	PRIMARY KEY("cod_finalidad")
);

CREATE TABLE IF NOT EXISTS "cat_condicion_salida" (
	"cod_condicion_salida" VARCHAR(2),
	"nombre" VARCHAR(30) NOT NULL,
	PRIMARY KEY("cod_condicion_salida")
);

CREATE TABLE IF NOT EXISTS "cat_tipo_incapacidad" (
	"cod_tipo_incapacidad" VARCHAR(2),
	"nombre" VARCHAR(30) NOT NULL,
	PRIMARY KEY("cod_tipo_incapacidad")
);

CREATE TABLE IF NOT EXISTS "prestador" (
	"cod_habilitacion" VARCHAR(12),
	"nombre" VARCHAR(120) NOT NULL,
	"id_sede" INTEGER NOT NULL,
	PRIMARY KEY("cod_habilitacion")
);

CREATE TABLE IF NOT EXISTS "profesional_salud" (
	"id_profesional" SERIAL,
	"cod_tipo_documento" VARCHAR(2) NOT NULL,
	"numero_documento" VARCHAR(20) NOT NULL,
	"nombre_completo" VARCHAR(150) NOT NULL,
	"registro_medico" VARCHAR(30),
	"id_sede" INTEGER NOT NULL,
	PRIMARY KEY("id_profesional"),
	CONSTRAINT "profesional_salud_unique_0" UNIQUE ("cod_tipo_documento", "numero_documento")
);

CREATE TABLE IF NOT EXISTS "usuario" (
	"id_usuario" SERIAL,
	"cod_tipo_documento" VARCHAR(2) NOT NULL,
	"numero_documento" VARCHAR(20) NOT NULL,
	"cod_pais_nacionalidad" VARCHAR(3) NOT NULL,
	"primer_nombre" VARCHAR(50) NOT NULL,
	"segundo_nombre" VARCHAR(50),
	"primer_apellido" VARCHAR(50) NOT NULL,
	"segundo_apellido" VARCHAR(50),
	"fecha_nacimiento" DATE NOT NULL,
	"cod_sexo" VARCHAR(1) NOT NULL,
	"cod_genero" VARCHAR(2),
	"cod_ocupacion" VARCHAR(10),
	"voluntad_anticipada" BOOLEAN,
	"cod_discapacidad" VARCHAR(2),
	"cod_etnia" VARCHAR(2),
	"id_comunidad_etnica" INTEGER,
	"cod_pais_residencia" VARCHAR(3) NOT NULL,
	"cod_municipio_residencia" VARCHAR(5) NOT NULL,
	"cod_zona" VARCHAR(1) NOT NULL,
	"direccion_residencia" VARCHAR(200) NOT NULL,
	"telefono" VARCHAR(20),
	"correo" VARCHAR(120),
	"id_sede_origen" INTEGER NOT NULL,
	"fhir_patient_id" VARCHAR(36),
	PRIMARY KEY("id_usuario"),
	CONSTRAINT "usuario_unique_0" UNIQUE ("cod_tipo_documento", "numero_documento", "id_sede_origen")
);

CREATE TABLE IF NOT EXISTS "contacto_responsable" (
	"id_responsable" SERIAL,
	"id_usuario" INTEGER NOT NULL,
	"nombre" VARCHAR(120) NOT NULL,
	"cod_parentesco" VARCHAR(2),
	"telefono" VARCHAR(20),
	PRIMARY KEY("id_responsable")
);

CREATE TABLE IF NOT EXISTS "alergia" (
	"id_alergia" SERIAL,
	"id_usuario" INTEGER NOT NULL,
	"sustancia" VARCHAR(120) NOT NULL,
	PRIMARY KEY("id_alergia")
);

CREATE TABLE IF NOT EXISTS "antecedente_familiar" (
	"id_antecedente" SERIAL,
	"id_usuario" INTEGER NOT NULL,
	"cod_parentesco" VARCHAR(2),
	"condicion" VARCHAR(150) NOT NULL,
	PRIMARY KEY("id_antecedente")
);

CREATE TABLE IF NOT EXISTS "riesgo_ocupacional" (
	"id_riesgo" SERIAL,
	"id_usuario" INTEGER NOT NULL,
	"descripcion" VARCHAR(150) NOT NULL,
	PRIMARY KEY("id_riesgo")
);

CREATE TABLE IF NOT EXISTS "atencion" (
	"id_atencion" SERIAL,
	"id_usuario" INTEGER NOT NULL,
	"cod_habilitacion" VARCHAR(12) NOT NULL,
	"cod_entidad" VARCHAR(10) NOT NULL,
	"fecha_hora_ingreso" TIMESTAMP NOT NULL,
	"cod_modalidad" VARCHAR(2) NOT NULL,
	"cod_entorno" VARCHAR(2) NOT NULL,
	"cod_via_ingreso" VARCHAR(2) NOT NULL,
	"causa_atencion" TEXT NOT NULL,
	PRIMARY KEY("id_atencion")
);

CREATE TABLE IF NOT EXISTS "triage" (
	"id_atencion" INTEGER,
	"fecha_hora_triage" TIMESTAMP NOT NULL,
	"cod_triage" VARCHAR(3) NOT NULL,
	PRIMARY KEY("id_atencion")
);

CREATE TABLE IF NOT EXISTS "diagnostico" (
	"id_diagnostico" SERIAL,
	"id_atencion" INTEGER NOT NULL,
	"cod_cie10" VARCHAR(8) NOT NULL,
	"momento" VARCHAR(10) NOT NULL,
	"tipo" VARCHAR(12) NOT NULL,
	PRIMARY KEY("id_diagnostico")
);

CREATE TABLE IF NOT EXISTS "tecnologia_salud" (
	"id_tecnologia" SERIAL,
	"id_atencion" INTEGER NOT NULL,
	"id_profesional" INTEGER NOT NULL,
	"id_medicamento" INTEGER NOT NULL,
	"dosis_cantidad" NUMERIC(10,2),
	"cod_unidad_medida" VARCHAR(10),
	"cod_via_admin" VARCHAR(3),
	"frecuencia_valor" INTEGER,
	"cod_unidad_tiempo" VARCHAR(3),
	"dias_tratamiento" INTEGER,
	"unidades_aplicadas" INTEGER,
	"cod_finalidad" VARCHAR(2),
	PRIMARY KEY("id_tecnologia")
);

CREATE TABLE IF NOT EXISTS "egreso" (
	"id_atencion" INTEGER,
	"fecha_hora_salida" TIMESTAMP NOT NULL,
	"cod_condicion_salida" VARCHAR(2) NOT NULL,
	"id_profesional_responsable" INTEGER NOT NULL,
	PRIMARY KEY("id_atencion")
);

CREATE TABLE IF NOT EXISTS "incapacidad" (
	"id_atencion" INTEGER,
	"cod_tipo_incapacidad" VARCHAR(2),
	"dias_incapacidad" INTEGER,
	"dias_licencia_maternidad" INTEGER,
	PRIMARY KEY("id_atencion")
);

CREATE TABLE IF NOT EXISTS "identidad_federada" (
	"id_mpi" SERIAL,
	"score_coincidencia" NUMERIC(3,2) NOT NULL,
	"fecha_resolucion" TIMESTAMP NOT NULL,
	PRIMARY KEY("id_mpi")
);

CREATE TABLE IF NOT EXISTS "identidad_federada_miembro" (
	"id_mpi" INTEGER NOT NULL,
	"id_usuario" INTEGER NOT NULL,
	PRIMARY KEY("id_mpi", "id_usuario")
);

ALTER TABLE "cat_municipio"
ADD FOREIGN KEY("cod_departamento") REFERENCES "cat_departamento"("cod_departamento")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "cat_comunidad_etnica"
ADD FOREIGN KEY("cod_etnia") REFERENCES "cat_etnia"("cod_etnia")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "prestador"
ADD FOREIGN KEY("id_sede") REFERENCES "sede"("id_sede")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "profesional_salud"
ADD FOREIGN KEY("cod_tipo_documento") REFERENCES "cat_tipo_documento"("cod_tipo_documento")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "profesional_salud"
ADD FOREIGN KEY("id_sede") REFERENCES "sede"("id_sede")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_tipo_documento") REFERENCES "cat_tipo_documento"("cod_tipo_documento")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_pais_nacionalidad") REFERENCES "cat_pais"("cod_pais")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_sexo") REFERENCES "cat_sexo"("cod_sexo")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_genero") REFERENCES "cat_genero"("cod_genero")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_ocupacion") REFERENCES "cat_ocupacion"("cod_ocupacion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_discapacidad") REFERENCES "cat_discapacidad"("cod_discapacidad")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_etnia") REFERENCES "cat_etnia"("cod_etnia")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("id_comunidad_etnica") REFERENCES "cat_comunidad_etnica"("id_comunidad_etnica")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_pais_residencia") REFERENCES "cat_pais"("cod_pais")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_municipio_residencia") REFERENCES "cat_municipio"("cod_municipio")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("cod_zona") REFERENCES "cat_zona"("cod_zona")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "usuario"
ADD FOREIGN KEY("id_sede_origen") REFERENCES "sede"("id_sede")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "contacto_responsable"
ADD FOREIGN KEY("id_usuario") REFERENCES "usuario"("id_usuario")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "contacto_responsable"
ADD FOREIGN KEY("cod_parentesco") REFERENCES "cat_parentesco"("cod_parentesco")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "alergia"
ADD FOREIGN KEY("id_usuario") REFERENCES "usuario"("id_usuario")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "antecedente_familiar"
ADD FOREIGN KEY("id_usuario") REFERENCES "usuario"("id_usuario")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "antecedente_familiar"
ADD FOREIGN KEY("cod_parentesco") REFERENCES "cat_parentesco"("cod_parentesco")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "riesgo_ocupacional"
ADD FOREIGN KEY("id_usuario") REFERENCES "usuario"("id_usuario")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "atencion"
ADD FOREIGN KEY("id_usuario") REFERENCES "usuario"("id_usuario")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "atencion"
ADD FOREIGN KEY("cod_habilitacion") REFERENCES "prestador"("cod_habilitacion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "atencion"
ADD FOREIGN KEY("cod_entidad") REFERENCES "cat_entidad_salud"("cod_entidad")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "atencion"
ADD FOREIGN KEY("cod_modalidad") REFERENCES "cat_modalidad"("cod_modalidad")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "atencion"
ADD FOREIGN KEY("cod_entorno") REFERENCES "cat_entorno"("cod_entorno")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "atencion"
ADD FOREIGN KEY("cod_via_ingreso") REFERENCES "cat_via_ingreso"("cod_via_ingreso")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "triage"
ADD FOREIGN KEY("id_atencion") REFERENCES "atencion"("id_atencion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "triage"
ADD FOREIGN KEY("cod_triage") REFERENCES "cat_clasificacion_triage"("cod_triage")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "diagnostico"
ADD FOREIGN KEY("id_atencion") REFERENCES "atencion"("id_atencion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "diagnostico"
ADD FOREIGN KEY("cod_cie10") REFERENCES "cat_cie10"("cod_cie10")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("id_atencion") REFERENCES "atencion"("id_atencion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("id_profesional") REFERENCES "profesional_salud"("id_profesional")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("id_medicamento") REFERENCES "cat_medicamento"("id_medicamento")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("cod_unidad_medida") REFERENCES "cat_unidad_medida"("cod_unidad_medida")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("cod_via_admin") REFERENCES "cat_via_administracion"("cod_via_admin")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("cod_unidad_tiempo") REFERENCES "cat_unidad_tiempo"("cod_unidad_tiempo")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "tecnologia_salud"
ADD FOREIGN KEY("cod_finalidad") REFERENCES "cat_finalidad"("cod_finalidad")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "egreso"
ADD FOREIGN KEY("id_atencion") REFERENCES "atencion"("id_atencion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "egreso"
ADD FOREIGN KEY("cod_condicion_salida") REFERENCES "cat_condicion_salida"("cod_condicion_salida")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "egreso"
ADD FOREIGN KEY("id_profesional_responsable") REFERENCES "profesional_salud"("id_profesional")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "incapacidad"
ADD FOREIGN KEY("id_atencion") REFERENCES "egreso"("id_atencion")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "incapacidad"
ADD FOREIGN KEY("cod_tipo_incapacidad") REFERENCES "cat_tipo_incapacidad"("cod_tipo_incapacidad")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "identidad_federada_miembro"
ADD FOREIGN KEY("id_mpi") REFERENCES "identidad_federada"("id_mpi")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "identidad_federada_miembro"
ADD FOREIGN KEY("id_usuario") REFERENCES "usuario"("id_usuario")
ON UPDATE NO ACTION ON DELETE NO ACTION;