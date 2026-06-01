## Registro de Desarrollo TFG: Motor de Recomendaciones (MLPClassifier)

**Fecha:** Junio 2026
**Objetivo:** Documentar la evolución, problemas detectados y soluciones implementadas en el modelo predictivo del motor de recomendaciones.

### 1. Arquitectura Inicial del Modelo
* **Algoritmo:** Red Neuronal Perceptrón Multicapa (`MLPClassifier` de `scikit-learn`).
* **Estructura inicial de datos:** Vector de 9 características (3 métricas de actividad y 6 calificaciones).
* **Problema detectado (Falso Positivo de Repaso):** El modelo interpretaba el valor `-1.0`, utilizado para representar "tema no cursado", como una calificación deficiente. Esto provocaba que el sistema recomendara erróneamente repasar temas que el alumno aún no había comenzado.

### 2. Primera Iteración: Rediseño del Vector de Características
* **Solución implementada:** Se reestructuró la entrada del modelo para separar el rendimiento académico del progreso en el temario.
* **Nueva estructura (15 características):** * 3 métricas de actividad (días activos, interacciones, conceptos aprendidos).
    * 6 indicadores binarios (1 = tema cursado, 0 = tema no cursado).
    * 6 calificaciones limpias (sustituyendo los `-1.0` por `0.0` para no sesgar a la red neuronal).
* **Resultado:** Eliminación del sesgo negativo de los temas no cursados.

### 3. Segunda Iteración: Corrección de Desbalanceo de Clases (Class Imbalance)
* **Problema detectado:** Al utilizar un vector con todos los temas aprobados, el modelo recomendaba `avanzar_siguiente_tema` en lugar de `hacer_examen_global`.
* **Causa raíz:** La generación puramente aleatoria de datos sintéticos producía una cantidad ínfima (menos del 1%) de casos donde un estudiante aprobaba los 6 temas. El modelo no tenía suficientes ejemplos para aprender a predecir la clase minoritaria.
* **Solución implementada:** Se ajustó el script de generación de datos para forzar que el 20% de las 5000 muestras de entrenamiento correspondieran matemáticamente a "casos de éxito total".

### 4. Tercera Iteración: Prevención de Aprendizaje de Atajo (Shortcut Learning)
* **Problema detectado:** Tras el balanceo anterior, el modelo comenzó a recomendar el examen global basándose únicamente en los 6 indicadores binarios (temario completo), ignorando si había notas suspensas en esos temas.
* **Causa raíz:** La red neuronal aprendió la regla más sencilla (si hay seis `1` seguidos, es examen global) debido a la falta de contraejemplos de alumnos que terminan el temario pero suspenden.
* **Solución implementada:** Se introdujo un "Balanceo de 3 Vías" en la generación de datos de entrenamiento:
    * **20% Éxito total:** Temario completo y todo aprobado (etiqueta: `hacer_examen_global`).
    * **20% Contraejemplos:** Temario completo pero con alguna nota suspensa (etiqueta: `repasar_tema_X`).
    * **60% Progreso normal:** Temario incompleto con avance o repaso según la nota (etiqueta: `avanzar_siguiente_tema` o `repasar_tema_X`).
* **Ajuste de hiperparámetros:** Se aumentó el número de iteraciones máximas del modelo (`max_iter=1500`) para asegurar la convergencia ante la nueva complejidad de los datos.

### 5. Conclusión y Estado Final
El modelo final demostró ser robusto y preciso, capaz de interpretar correctamente el contexto del alumno (qué temas ha visto y qué notas ha sacado) sin caer en sesgos estadísticos. Evalúa correctamente los contraejemplos y emite recomendaciones coherentes con las reglas de negocio educativas planteadas en el proyecto.