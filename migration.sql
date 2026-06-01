-- ============================================================
-- Insertar Cuestionario de Ejercicios Prácticos (Tema 1)
-- ============================================================
INSERT INTO CUESTIONARIOS (tema_id, titulo, tipo) VALUES 
((SELECT id FROM TEMAS WHERE numero = 1 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')), 'Ejercicios Tema 1', 'practica');

-- Pregunta 1
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 1' AND tipo = 'practica'), 
 '1. Un sistema tiene una jerarquía de protocolos de 4 capas. Si genera mensajes de 2000 bytes y cada capa añade una cabecera de 32 bytes. ¿Qué fracción del ancho de banda se rellena con cabeceras?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Un sistema tiene una jerarqu%2000%'), 'A) aproximadamente el 94%', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Un sistema tiene una jerarqu%2000%'), 'B) aproximadamente 6%', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Un sistema tiene una jerarqu%2000%'), 'C) Ninguna es correcta', FALSE);

-- Pregunta 2
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 1' AND tipo = 'practica'), 
 '2. Un sistema tiene una jerarquía de protocolos de 4 capas. Si genera mensajes de 1500 bytes y cada capa añade una cabecera de 32 bytes. ¿Qué fracción del ancho de banda se rellena con información del mensaje a enviar?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Un sistema tiene una jerarqu%1500%'), 'A) Ninguna es correcta', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Un sistema tiene una jerarqu%1500%'), 'B) aproximadamente el 8%', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Un sistema tiene una jerarqu%1500%'), 'C) aproximadamente 92%', TRUE);


-- ============================================================
-- Insertar Cuestionario de Ejercicios Prácticos (Tema 3)
-- ============================================================
INSERT INTO CUESTIONARIOS (tema_id, titulo, tipo) VALUES 
((SELECT id FROM TEMAS WHERE numero = 3 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')), 'Ejercicios Tema 3', 'practica');

-- Pregunta 1
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 3' AND tipo = 'practica'), 
 '1. Dada la dirección IP 201.152.80.43 y la máscara 255.255.255.240. ¿Cuál es la dirección de subred y la dirección de broadcast de la subred?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Dada la dirección IP 201.152.80.43%'), 'A) 201.152.80.0 y 201.152.80.255, respectivamente', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Dada la dirección IP 201.152.80.43%'), 'B) 201.152.80.32 y 201.152.80.47, respectivamente', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Dada la dirección IP 201.152.80.43%'), 'C) 201.152.80.32 y 201.152.80.63, respectivamente', FALSE);

-- Pregunta 2
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 3' AND tipo = 'practica'), 
 '2. ¿Cuál de estas direcciones es una de las abreviaturas más corta para la dirección IPv6: 3FFE : 1044 : 0000 : 0000 : 00AB : 0000 : 0000 : 0057?', 
 NULL, 'alta');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. ¿Cuál de estas direcciones es una%'), 'A) 3FFE : 1044 :: 00AB :: 0057', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. ¿Cuál de estas direcciones es una%'), 'B) 3FFE : 1044 :: AB :: 57', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. ¿Cuál de estas direcciones es una%'), 'C) 3FFE : 1044 : 0 : 0 : AB :: 57', TRUE);

-- Pregunta 3
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 3' AND tipo = 'practica'), 
 '3. Dada la dirección IP 192.168.80.41 y la máscara 255.255.255.240. ¿Cuál es la dirección de subred?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Dada la dirección IP 192.168.80.41%'), 'A) 192.168.80.0', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Dada la dirección IP 192.168.80.41%'), 'B) 192.168.80.40', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Dada la dirección IP 192.168.80.41%'), 'C) 192.168.80.32', TRUE);

-- Pregunta 4
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 3' AND tipo = 'practica'), 
 '4. Dada la dirección de red 192.168.30.32/28. ¿Cuál sería la dirección de difusión de dicha red?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '4. Dada la dirección de red 192.168.30.32/28%'), 'A) 192.168.31.255', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '4. Dada la dirección de red 192.168.30.32/28%'), 'B) 192.168.30.47', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '4. Dada la dirección de red 192.168.30.32/28%'), 'C) 192.168.30.127', FALSE);

-- ============================================================
-- Insertar Cuestionario de Ejercicios Prácticos (Tema 4)
-- ============================================================
INSERT INTO CUESTIONARIOS (tema_id, titulo, tipo) VALUES 
((SELECT id FROM TEMAS WHERE numero = 4 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')), 'Ejercicios Tema 4', 'practica');

-- Pregunta 1
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 4' AND tipo = 'practica'), 
 '1. Si un paquete IP de 1020 bytes llega a un enrutador que debe fragmentarlo en ocho trozos, ¿cuánto sumará las longitudes de todos los fragmentos producidos?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Si un paquete IP de 1020%'), 'A) 1160', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Si un paquete IP de 1020%'), 'B) 1080', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Si un paquete IP de 1020%'), 'C) 1200', FALSE);

-- Pregunta 2
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 4' AND tipo = 'practica'), 
 '2. Si un paquete IP de 1040 bytes llega a un enrutador que debe fragmentarlo en siete paquetes, ¿cuánto sumará las longitudes de todos los fragmentos producidos incluida sus cabeceras?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Si un paquete IP de 1040%'), 'A) 1060', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Si un paquete IP de 1040%'), 'B) 1200', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Si un paquete IP de 1040%'), 'C) 1140', TRUE);

-- Pregunta 3
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 4' AND tipo = 'practica'), 
 '3. Si un enrutador recibe por la interfaz conectada a la red A, un paquete IP de 1600 bytes y debe transmitirlo por una interfaz cuya MTU es 572, ¿en cuántos paquetes tendrá que fragmentar el paquete recibido?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Si un enrutador recibe por la interfaz conectada a la red A, un paquete IP de 1600%'), 'A) Ninguna es correcta.', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Si un enrutador recibe por la interfaz conectada a la red A, un paquete IP de 1600%'), 'B) Dos paquetes de 572 y uno de 496.', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Si un enrutador recibe por la interfaz conectada a la red A, un paquete IP de 1600%'), 'C) Dos paquetes de 572 y uno de 456.', FALSE);

-- Pregunta 4
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 4' AND tipo = 'practica'), 
 '4. Si un enrutador recibe un paquete IP de 1100 bytes y debe transmitirlo por una interfaz cuya MTU es 520, ¿en cuántos paquetes tendrá que fragmentar el paquete recibido?', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '4. Si un enrutador recibe un paquete IP de 1100%'), 'A) No es necesario fragmentar.', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '4. Si un enrutador recibe un paquete IP de 1100%'), 'B) 2.', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '4. Si un enrutador recibe un paquete IP de 1100%'), 'C) 3.', TRUE);


-- ============================================================
-- Insertar Cuestionario de Ejercicios Prácticos (Tema 5)
-- ============================================================
INSERT INTO CUESTIONARIOS (tema_id, titulo, tipo) VALUES 
((SELECT id FROM TEMAS WHERE numero = 5 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')), 'Ejercicios Tema 5', 'practica');

-- Pregunta 1
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 5' AND tipo = 'practica'), 
 '1. Suponga que A establece, mediante el saludo de tres vías de TCP, una conexión con B. Los números de secuencia elegidos por A y B son, respectivamente, 750 y 600. Una vez establecida la conexión A le envía un primer segmento con 10 bytes de datos a B. Diga cuáles serán los valores de número de secuencia y ACK (acuse de recibo) que llevará la cabecera TCP de ese primer segmento con datos:', 
 NULL, 'alta');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Suponga que A establece%750%600%'), 'A) Secuencia 750, ACK 600', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Suponga que A establece%750%600%'), 'B) Secuencia 761, ACK 601', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Suponga que A establece%750%600%'), 'C) Secuencia 751, ACK 601', TRUE);

-- Pregunta 2
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 5' AND tipo = 'practica'), 
 '2. Supón que utilizas inicio lento (slow-start) en una línea con un tiempo de ida y vuelta (RTT) de 10 ms. La ventana receptora es de 32Kbytes y el tamaño máximo de segmento es de 1KB. ¿Cuánto tiempo pasará antes de poder enviar la primera ventana completa? Supón que no se produce congestión.', 
 NULL, 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Supón que utilizas inicio lento%10 ms%'), 'A) 60 ms', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Supón que utilizas inicio lento%10 ms%'), 'B) 50 ms', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Supón que utilizas inicio lento%10 ms%'), 'C) Ninguna es correcta', FALSE);

-- Pregunta 3
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 5' AND tipo = 'practica'), 
 '3. Un emisor ha enviado los segmentos 1 al 30. Cada uno de ellos con 512 bytes de datos. El emisor recibe un ACK con valor 5121 (10x512=5120), y después 3 ACKs duplicados con valor 5633. Basándose en esta información, ¿qué segmento puede asumir el emisor que se han perdido?', 
 NULL, 'alta');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Un emisor ha enviado los segmentos 1 al 30%'), 'A) Segmento 10', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Un emisor ha enviado los segmentos 1 al 30%'), 'B) Segmento 11', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Un emisor ha enviado los segmentos 1 al 30%'), 'C) Segmento 12', TRUE);
