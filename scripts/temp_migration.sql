-- Insertar Cuestionario de Ejercicios Prácticos (Tema 2)
INSERT INTO CUESTIONARIOS (tema_id, titulo, tipo) VALUES 
((SELECT id FROM TEMAS WHERE numero = 2 AND asignatura_id = (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes')), 'Ejercicios Tema 2', 'practica');

-- Pregunta 1 (Dijkstra)
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 2' AND tipo = 'practica'), 
 '1. Aplique Dijkstra para determinar el costo de la ruta de menor coste entre O y T del grafo que se muestra en la figura. El valor del coste de cada enlace aparece representado en cada enlace.', 
 'https://i.imgur.com/b0fLQoQ.png', 'alta');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Aplique Dijkstra%'), 'A) 13', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Aplique Dijkstra%'), 'B) 16', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '1. Aplique Dijkstra%'), 'C) Ninguna de las anteriores', FALSE);

-- Pregunta 2 (Encaminamiento)
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 2' AND tipo = 'practica'), 
 '2. Suponga que se utiliza un algoritmo de encaminamiento de vector distancia, y el enrutador C recibe los siguientes vectores de encaminamiento de sus vecinos (B, D y E): desde B(8,0,10,9,15,20), desde D(8,10,3,0,15,10) y desde E(10,5,12,6,0,8). Cada vector representa sus retardos a los nodos A, B, C, D, E y F respectivamente. Los retardos medidos a B, D y E son, respectivamente, 5, 6 y 10. De acuerdo a dicha información, en la tabla de enrutamiento que generaría el enrutador C, ¿por dónde encaminaría los paquetes dirigidos a A?', 
 NULL, 'alta');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Suponga que se utiliza%'), 'A) D', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Suponga que se utiliza%'), 'B) B', TRUE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '2. Suponga que se utiliza%'), 'C) E', FALSE);

-- Pregunta 3 (Rutas)
INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto, imagen_url, dificultad) VALUES 
((SELECT id FROM CUESTIONARIOS WHERE titulo = 'Ejercicios Tema 2' AND tipo = 'practica'), 
 '3. Indique el número de rutas que toma un paquete enviado de A a F usando inundación, y estableciendo un número de saltos máximo 2. Se considera una ruta, el envío de un origen a un destino que no reenvía dicho paquete.', 
 'https://i.imgur.com/LrUwsnA.png', 'media');

INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta) VALUES 
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Indique el número de rutas%'), 'A) 10', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Indique el número de rutas%'), 'B) Ninguna de las anteriores', FALSE),
((SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE pregunta_texto LIKE '3. Indique el número de rutas%'), 'C) 4', TRUE);
