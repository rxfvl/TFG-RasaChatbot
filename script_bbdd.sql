-- ============================================================
-- 1. TABLAS INDEPENDIENTES (Sin Claves Foráneas)
-- ============================================================

CREATE TABLE ALUMNOS (
    rasa_sender_id VARCHAR(255) PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    correo         VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE PROFESORES (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE ASIGNATURAS (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(150) NOT NULL,
    titulacion          VARCHAR(150),
    curso               VARCHAR(50),
    enlace_guia_docente VARCHAR(255)
);


-- ============================================================
-- 2. TABLAS CON DEPENDENCIAS DIRECTAS (Nivel 1)
-- ============================================================

CREATE TABLE MATRICULAS (
    alumno_id    VARCHAR(255) NOT NULL,
    asignatura_id INT         NOT NULL,
    PRIMARY KEY (alumno_id, asignatura_id),
    FOREIGN KEY (alumno_id)     REFERENCES ALUMNOS(rasa_sender_id) ON DELETE CASCADE,
    FOREIGN KEY (asignatura_id) REFERENCES ASIGNATURAS(id)         ON DELETE CASCADE
);

CREATE TABLE PROF_ASIG (
    profesor_id   INT NOT NULL,
    asignatura_id INT NOT NULL,
    PRIMARY KEY (profesor_id, asignatura_id),
    FOREIGN KEY (profesor_id)   REFERENCES PROFESORES(id)   ON DELETE CASCADE,
    FOREIGN KEY (asignatura_id) REFERENCES ASIGNATURAS(id)  ON DELETE CASCADE
);

CREATE TABLE TEMAS (
    id            SERIAL PRIMARY KEY,
    asignatura_id INT          NOT NULL,
    numero        INT          NOT NULL,
    titulo        VARCHAR(150) NOT NULL,
    UNIQUE (asignatura_id, numero),
    FOREIGN KEY (asignatura_id) REFERENCES ASIGNATURAS(id) ON DELETE CASCADE
);

CREATE TABLE CLASE_HORARIO (
    id            SERIAL PRIMARY KEY,
    profesor_id   INT,
    asignatura_id INT NOT NULL,
    grupo         VARCHAR(10) CHECK (grupo IN ('GG1', 'GG2', 'GM1', 'GM2', 'GM3')),
    dia_semana    VARCHAR(10) CHECK (dia_semana IN ('lunes', 'martes', 'miercoles', 'jueves', 'viernes')),
    hora_inicio   TIME,
    hora_fin      TIME,
    CONSTRAINT clase_horas_check CHECK (hora_fin > hora_inicio),
    FOREIGN KEY (profesor_id)   REFERENCES PROFESORES(id)   ON DELETE SET NULL,
    FOREIGN KEY (asignatura_id) REFERENCES ASIGNATURAS(id)  ON DELETE CASCADE
);

CREATE TABLE ENTREGAS_CALENDARIO (
    id            SERIAL PRIMARY KEY,
    profesor_id   INT,
    asignatura_id INT          NOT NULL,
    titulo        VARCHAR(150) NOT NULL,
    descripcion   TEXT,
    fecha_limite  DATE,
    FOREIGN KEY (profesor_id)   REFERENCES PROFESORES(id)   ON DELETE SET NULL,
    FOREIGN KEY (asignatura_id) REFERENCES ASIGNATURAS(id)  ON DELETE CASCADE
);

CREATE TABLE TUTORIAS (
    id          SERIAL PRIMARY KEY,
    profesor_id INT         NOT NULL,
    dia_semana  VARCHAR(10) NOT NULL CHECK (dia_semana IN ('lunes', 'martes', 'miercoles', 'jueves', 'viernes')),
    hora_inicio TIME        NOT NULL,
    hora_fin    TIME        NOT NULL,
    CONSTRAINT tutorias_horas_check CHECK (hora_fin > hora_inicio),
    FOREIGN KEY (profesor_id) REFERENCES PROFESORES(id) ON DELETE CASCADE
);

CREATE TABLE INTERACCIONES_CHAT (
    id            SERIAL PRIMARY KEY,
    alumno_id     VARCHAR(255),
    tipo_consulta VARCHAR(100),
    mensaje_usuario TEXT,
    fecha         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alumno_id) REFERENCES ALUMNOS(rasa_sender_id) ON DELETE SET NULL
);


-- ============================================================
-- 3. TABLAS DEPENDIENTES DE TEMAS (Nivel 2)
-- ============================================================

CREATE TABLE CONCEPTOS_TEORICOS (
    id         SERIAL PRIMARY KEY,
    tema_id    INT          NOT NULL,
    termino    VARCHAR(100) NOT NULL,
    definicion TEXT         NOT NULL,
    FOREIGN KEY (tema_id) REFERENCES TEMAS(id) ON DELETE CASCADE
);

CREATE TABLE CUESTIONARIOS (
    id      SERIAL PRIMARY KEY,
    tema_id INT          NOT NULL,
    titulo  VARCHAR(150) NOT NULL,
    FOREIGN KEY (tema_id) REFERENCES TEMAS(id) ON DELETE CASCADE
);


-- ============================================================
-- 4. TABLAS DE PREGUNTAS Y SEGUIMIENTO (Nivel 3)
-- ============================================================

CREATE TABLE CUESTIONARIOS_PREGUNTAS (
    id                     SERIAL PRIMARY KEY,
    cuestionario_id        INT  NOT NULL,
    concepto_relacionado_id INT,
    pregunta_texto         TEXT NOT NULL,
    dificultad             VARCHAR(10) DEFAULT 'media'
                               CHECK (dificultad IN ('baja', 'media', 'alta')),
    FOREIGN KEY (cuestionario_id)         REFERENCES CUESTIONARIOS(id)       ON DELETE CASCADE,
    FOREIGN KEY (concepto_relacionado_id) REFERENCES CONCEPTOS_TEORICOS(id)  ON DELETE SET NULL
);

CREATE TABLE SEGUIMIENTO (
    id              SERIAL PRIMARY KEY,
    alumno_id       VARCHAR(255) NOT NULL,
    cuestionario_id INT          NOT NULL,
    puntuacion_total REAL,
    fecha_intento   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alumno_id)       REFERENCES ALUMNOS(rasa_sender_id) ON DELETE CASCADE,
    FOREIGN KEY (cuestionario_id) REFERENCES CUESTIONARIOS(id)       ON DELETE CASCADE
);


-- ============================================================
-- 5. TABLAS DE RESPUESTAS Y DETALLES (Nivel 4)
-- ============================================================

CREATE TABLE CUESTIONARIOS_RESPUESTAS (
    id           SERIAL PRIMARY KEY,
    pregunta_id  INT  NOT NULL,
    texto_opcion TEXT NOT NULL,
    es_correcta  BOOLEAN NOT NULL DEFAULT FALSE,
    feedback     TEXT,
    FOREIGN KEY (pregunta_id) REFERENCES CUESTIONARIOS_PREGUNTAS(id) ON DELETE CASCADE
);

CREATE TABLE SEGUIMIENTO_DETALLE (
    id             SERIAL PRIMARY KEY,
    seguimiento_id INT NOT NULL,
    pregunta_id    INT NOT NULL,
    respuesta_id   INT NOT NULL,
    UNIQUE (seguimiento_id, pregunta_id),
    FOREIGN KEY (seguimiento_id) REFERENCES SEGUIMIENTO(id)               ON DELETE CASCADE,
    FOREIGN KEY (pregunta_id)    REFERENCES CUESTIONARIOS_PREGUNTAS(id)   ON DELETE CASCADE,
    FOREIGN KEY (respuesta_id)   REFERENCES CUESTIONARIOS_RESPUESTAS(id)  ON DELETE CASCADE
);


-- ============================================================
-- 6. ÍNDICES
-- ============================================================

-- MATRICULAS
CREATE INDEX idx_matriculas_alumno      ON MATRICULAS(alumno_id);
CREATE INDEX idx_matriculas_asignatura  ON MATRICULAS(asignatura_id);

-- PROF_ASIG
CREATE INDEX idx_prof_asig_profesor     ON PROF_ASIG(profesor_id);
CREATE INDEX idx_prof_asig_asignatura   ON PROF_ASIG(asignatura_id);

-- TEMAS
CREATE INDEX idx_temas_asignatura       ON TEMAS(asignatura_id);

-- CLASE_HORARIO
CREATE INDEX idx_clase_horario_profesor    ON CLASE_HORARIO(profesor_id);
CREATE INDEX idx_clase_horario_asignatura  ON CLASE_HORARIO(asignatura_id);
CREATE INDEX idx_clase_horario_grupo       ON CLASE_HORARIO(grupo);
-- Consultas de franjas horarias ("¿qué clases hay el lunes?")
CREATE INDEX idx_clase_horario_dia         ON CLASE_HORARIO(dia_semana);

-- ENTREGAS_CALENDARIO
CREATE INDEX idx_entregas_profesor         ON ENTREGAS_CALENDARIO(profesor_id);
CREATE INDEX idx_entregas_asignatura       ON ENTREGAS_CALENDARIO(asignatura_id);
-- Consultas por fecha límite ("entregas próximas")
CREATE INDEX idx_entregas_fecha_limite     ON ENTREGAS_CALENDARIO(fecha_limite);

-- TUTORIAS
CREATE INDEX idx_tutorias_profesor         ON TUTORIAS(profesor_id);
-- Consultas de disponibilidad por día y hora
CREATE INDEX idx_tutorias_dia_hora         ON TUTORIAS(dia_semana, hora_inicio, hora_fin);

-- INTERACCIONES_CHAT
CREATE INDEX idx_chat_alumno               ON INTERACCIONES_CHAT(alumno_id);
-- Consultas analíticas por fecha y tipo
CREATE INDEX idx_chat_fecha                ON INTERACCIONES_CHAT(fecha);
CREATE INDEX idx_chat_tipo_consulta        ON INTERACCIONES_CHAT(tipo_consulta);

-- CONCEPTOS_TEORICOS
CREATE INDEX idx_conceptos_tema            ON CONCEPTOS_TEORICOS(tema_id);

-- CUESTIONARIOS
CREATE INDEX idx_cuestionarios_tema        ON CUESTIONARIOS(tema_id);

-- CUESTIONARIOS_PREGUNTAS
CREATE INDEX idx_preguntas_cuestionario    ON CUESTIONARIOS_PREGUNTAS(cuestionario_id);
CREATE INDEX idx_preguntas_concepto        ON CUESTIONARIOS_PREGUNTAS(concepto_relacionado_id);
-- Filtrado por dificultad
CREATE INDEX idx_preguntas_dificultad      ON CUESTIONARIOS_PREGUNTAS(dificultad);

-- SEGUIMIENTO
CREATE INDEX idx_seguimiento_alumno        ON SEGUIMIENTO(alumno_id);
CREATE INDEX idx_seguimiento_cuestionario  ON SEGUIMIENTO(cuestionario_id);
-- Consultas de historial ordenado cronológicamente
CREATE INDEX idx_seguimiento_fecha         ON SEGUIMIENTO(fecha_intento);

-- CUESTIONARIOS_RESPUESTAS
CREATE INDEX idx_respuestas_pregunta       ON CUESTIONARIOS_RESPUESTAS(pregunta_id);

-- SEGUIMIENTO_DETALLE
CREATE INDEX idx_detalle_seguimiento       ON SEGUIMIENTO_DETALLE(seguimiento_id);
CREATE INDEX idx_detalle_pregunta          ON SEGUIMIENTO_DETALLE(pregunta_id);
CREATE INDEX idx_detalle_respuesta         ON SEGUIMIENTO_DETALLE(respuesta_id);
