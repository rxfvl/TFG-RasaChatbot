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
    tipo_consulta VARCHAR(100), -- Rasa intent
    mensaje_usuario TEXT,
    fecha         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alumno_id) REFERENCES ALUMNOS(rasa_sender_id) ON DELETE SET NULL
);


-- ============================================================
-- 3. TABLAS DEPENDIENTES DE TEMAS (Nivel 2)
-- ============================================================

CREATE TABLE CONCEPTOS_TEORICOS (
    id               SERIAL PRIMARY KEY,
    tema_id          INT          NOT NULL,
    termino          VARCHAR(100) NOT NULL,
    termino_legible  VARCHAR(150),
    definicion       TEXT         NOT NULL,
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

-- ============================================================
-- 7. DATOS INICIALES (INSERTS)
-- ============================================================

-- Insertar Profesora
INSERT INTO PROFESORES (nombre, correo) 
VALUES ('Amelia Zafra Gómez', 'in1zagoa@uco.es');

-- Insertar Asignatura
INSERT INTO ASIGNATURAS (nombre, titulacion, curso, enlace_guia_docente) 
VALUES ('Redes', 'Ingeniería Informática', 'tercero', '');


-- Asignar Profesora a la Asignatura
INSERT INTO PROF_ASIG (profesor_id, asignatura_id)
VALUES (
    (SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'),
    (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')
);

-- Alumno de prueba y su matrícula en Redes
-- (rasa_sender_id = Telegram user_id del alumno de desarrollo)
INSERT INTO ALUMNOS (rasa_sender_id, nombre, correo)
VALUES ('6266468745', 'Rafael David Tortosa Bueno', 'i22tobur@uco.es')
ON CONFLICT (rasa_sender_id) DO NOTHING;

INSERT INTO MATRICULAS (alumno_id, asignatura_id)
VALUES (
    '6266468745',
    (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')
)
ON CONFLICT DO NOTHING;

-- Insertar Temas (todos los temas del temario)
INSERT INTO TEMAS (asignatura_id, numero, titulo) VALUES
((SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 1, 'Tema 1'),
((SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 2, 'Tema 2'),
((SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 3, 'Tema 3'),
((SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 4, 'Tema 4'),
((SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 5, 'Tema 5'),
((SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 6, 'Tema 6')
ON CONFLICT (asignatura_id, numero) DO NOTHING;

-- Insertar Conceptos Teóricos extraídos del Material-Temario.pdf
-- (termino = slug interno, termino_legible = nombre mostrado al usuario)

-- TEMA 1: Introducción a las redes
INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES
((SELECT id FROM TEMAS WHERE numero = 1 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'sistema_comunicacion', 'Sistema de comunicación',
 'Un sistema de comunicación es un conjunto de elementos y dispositivos involucrados en el intercambio eficaz de información entre dos puntos remotos.'),

((SELECT id FROM TEMAS WHERE numero = 1 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'red_computadoras', 'Red de computadoras',
 'La red de computadoras es un conjunto de equipos terminales autónomos e interconectados.'),

((SELECT id FROM TEMAS WHERE numero = 1 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'servicio_capa', 'Servicio de capa',
 'El servicio que ofrece una capa indica qué hace la capa, qué servicios brinda a la capa superior. Define el aspecto semántico (significado) de la capa, no la forma en que la capa superior tiene acceso al servicio.'),

((SELECT id FROM TEMAS WHERE numero = 1 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'protocolo', 'Protocolo',
 'El protocolo es un conjunto de normas, o un acuerdo, que determina el formato y la transmisión de datos entre capas homólogas en equipos distintos. Son las reglas de comunicación entre capas idénticas.'),

((SELECT id FROM TEMAS WHERE numero = 1 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'modelo_referencia', 'Modelo de referencia',
 'El modelo de referencia es el conjunto de capas definido y las funciones asociadas al mismo.');

-- TEMA 2: Capa de Red (conmutación, enrutamiento, congestión)
INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES
((SELECT id FROM TEMAS WHERE numero = 2 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'conmutacion', 'Conmutación',
 'La Conmutación consiste en establecer un camino entre dos puntos, un emisor y un receptor a través de nodos y líneas de transmisión. La conmutación permite la entrega de la señal desde el origen hasta el destino requerido. Existen diferentes técnicas de conmutación según como se establezca dicho camino: circuitos y paquetes.'),

((SELECT id FROM TEMAS WHERE numero = 2 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'enrutamiento', 'Algoritmo de enrutamiento',
 'El algoritmo de enrutamiento es la parte de software de la capa de red encargada de decidir la línea de salida por la que se retransmite un paquete de entrada.'),

((SELECT id FROM TEMAS WHERE numero = 2 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'capa_red', 'Capa de Red',
 'La Capa de Red tiene entre sus funciones el encaminamiento, el control de congestión y la interconexión entre redes.'),

((SELECT id FROM TEMAS WHERE numero = 2 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'congestion', 'Congestión',
 'La congestión se produce cuando la carga (temporalmente) es superior (en una parte del sistema) a la que pueden manejar los recursos.'),

((SELECT id FROM TEMAS WHERE numero = 2 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'calidad_servicio', 'Calidad de servicio',
 'La calidad de servicio hace referencia a los procedimientos utilizados para gestionar el tráfico de una red y garantizar un cierto nivel de rendimiento según el tipo de aplicación.');

-- TEMA 3: Protocolo IP, NAT, DHCP
INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES
((SELECT id FROM TEMAS WHERE numero = 3 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'ip_caracteristicas', 'Protocolo IP',
 'Las principales características del protocolo IP son: es sin conexión, del mejor esfuerzo e independiente de los medios.'),

((SELECT id FROM TEMAS WHERE numero = 3 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'nat', 'NAT (Network Address Translation)',
 'La traducción de direcciones de red (NAT, Network Address Translation) es un mecanismo que permite traducir una dirección IP privada a una dirección IP pública de forma que los paquetes pertenecientes a un host puedan ser enrutados.'),

((SELECT id FROM TEMAS WHERE numero = 3 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'icmp', 'ICMP',
 'ICMP es un protocolo de mensajes de control en Internet, que entre otros eventos puede informar de: destino inalcanzable, tiempo excedido, mensajes de eco y respuesta.'),

((SELECT id FROM TEMAS WHERE numero = 3 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'dhcp', 'DHCP',
 'DHCP es un protocolo que permite asignar direcciones IP tanto de forma automática, como manual, como dinámica.'),

((SELECT id FROM TEMAS WHERE numero = 3 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'sistema_autonomo', 'Sistema autónomo',
 'Un sistema autónomo es un conjunto de subredes, y el hardware asociado, administradas por una única autoridad, de forma que en ella se puede implementar un algoritmo de encaminamiento independiente de los considerados en otros sistemas autónomos.');

-- TEMA 4: Dispositivos de red y fragmentación
INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES
((SELECT id FROM TEMAS WHERE numero = 4 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'repetidor', 'Repetidor',
 'Los repetidores (repeater) trabajan en el nivel físico, interconectando dos segmentos de LAN. Un repetidor, en cada dirección, regenera las señales eléctricas recibidas de un segmento y las reenvía al otro segmento.'),

((SELECT id FROM TEMAS WHERE numero = 4 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'hub', 'Hub',
 'Un hub es un multirepetidor operando a nivel de bit. Repiten los bits recibidos en una interfaz por todas las otras interfaces.'),

((SELECT id FROM TEMAS WHERE numero = 4 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'router', 'Router',
 'Un router (enrutador o encaminador) se trata de un dispositivo hardware o software para interconexión de redes de computadoras que opera en la capa tres (nivel de red) del modelo OSI. El router interconecta segmentos de red o redes enteras. Hace pasar paquetes de datos entre redes tomando como base la información de la capa de red.'),

((SELECT id FROM TEMAS WHERE numero = 4 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'tunelizacion', 'Tunelización',
 'La tunelización permite la interconexión entre host de origen y de destino que están en el mismo tipo de red, pero hay una red diferente en medio.'),

((SELECT id FROM TEMAS WHERE numero = 4 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'fragmentacion', 'Fragmentación de paquetes',
 'La fragmentación de paquetes puede ser transparente. La Fragmentación transparente resulta transparente para cualquier red subsecuente por la que deba pasar el paquete en su camino hacia el destino final debido a que se reensambla el paquete. En la fragmentación no transparente, una vez que se ha fragmentado un paquete, cada fragmento se trata como si fuera un paquete original. La recombinación ocurre sólo en el host de destino.');

-- TEMA 5: Capa de transporte, TCP, UDP
INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES
((SELECT id FROM TEMAS WHERE numero = 5 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'capa_transporte', 'Capa de transporte',
 'La capa de transporte se encarga de proporcionar un transporte de datos confiable, eficiente y económico de la máquina de origen a destino, independientemente de la red o redes físicas en uso.'),

((SELECT id FROM TEMAS WHERE numero = 5 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'udp', 'Protocolo UDP',
 'El protocolo UDP proporciona una forma para que las aplicaciones envíen datagramas IP encapsulados sin tener que establecer una conexión utilizando la política del mejor esfuerzo.'),

((SELECT id FROM TEMAS WHERE numero = 5 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'tcp', 'Protocolo TCP',
 'El protocolo TCP proporciona un flujo de bytes confiable de extremo a extremo a través de una interred no confiable.'),

((SELECT id FROM TEMAS WHERE numero = 5 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'iana', 'IANA',
 'La Autoridad de Números Asignados de Internet (IANA) es el organismo de estandarización que se encarga de asignar diversos estándares de direccionamiento, incluidos los números de puerto.'),

((SELECT id FROM TEMAS WHERE numero = 5 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'desempeno_transporte', 'Desempeño en la capa de transporte',
 'Se pueden considerar cuatro aspectos de desempeño a nivel de capa de transporte: los problemas del diseño en el desempeño, medición del desempeño, diseño de sistemas con mejor desempeño y procesamiento rápido de las unidades de datos del protocolo de transporte.');

-- TEMA 6: Capa de aplicación, DNS, HTTP, SMTP
INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES
((SELECT id FROM TEMAS WHERE numero = 6 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'capa_aplicacion', 'Capa de aplicación',
 'La capa de aplicación se encarga de definir los protocolos de aplicaciones que el usuario requiere con frecuencia.'),

((SELECT id FROM TEMAS WHERE numero = 6 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'dns', 'Protocolo DNS',
 'El protocolo DNS (Servidor de Nombres de Dominio) es un sistema de nomenclatura jerárquico descentralizado para dispositivos conectados a redes IP como Internet o una red privada. Este sistema asocia diferente información con los nombres de dominio asignados.'),

((SELECT id FROM TEMAS WHERE numero = 6 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'http', 'Protocolo HTTP',
 'El protocolo HTTP (Protocolo de Transferencia de Hipertexto) es un protocolo de comunicación que se emplea para transferir información a través de la World Wide Web.'),

((SELECT id FROM TEMAS WHERE numero = 6 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'smtp', 'Protocolo SMTP',
 'El protocolo SMTP (Protocolo para la Transferencia Simple de Correo) es un protocolo de red que se emplea para enviar y recibir correos electrónicos (emails).'),

((SELECT id FROM TEMAS WHERE numero = 6 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')),
 'streaming', 'Streaming multimedia',
 'Streaming multimedia significa que los datos se envían hacia el ordenador del cliente y se reproducen al mismo tiempo.');


