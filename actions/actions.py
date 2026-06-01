"""
Custom actions para el chatbot de Redes.

Arquitectura de conceptos teóricos:
  - action_listar_temas         → Muestra TODOS los temas (cuestionarios Y conceptos)
  - action_listar_conceptos     → Lista los conceptos de un tema desde la BBDD
  - action_dar_concepto         → Muestra la definición de un concepto (por ID de BBDD)

Arquitectura de cuestionarios:
  - action_listar_temas         → Compartido (muestra todos los temas)
  - action_reset_cuestionario_dinamico → Inicia el cuestionario de un tema
  - validate_cuestionario_dinamico_form → Gestiona el flujo pregunta a pregunta

Log de intenciones:
  - action_registrar_intent     → Registra en INTERACCIONES_CHAT el intent de cada mensaje
  - ActionDefaultFallback       → Sobrescrita para loguear intents no reconocidos

Control de acceso por asignatura:
  - action_check_matricula      → Verifica si el alumno está matriculado en la asignatura activa
"""

from typing import Any, Text, Dict, List
import json
import os
import re
import psycopg2
import numpy as np
import joblib

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, UserUtteranceReverted, ActiveLoop, FollowupAction
from rasa_sdk.executor import CollectingDispatcher


# ---------------------------------------------------------------------------
# Capa de acceso a datos (Data Access Layer)
# ---------------------------------------------------------------------------

def get_db_connection():
    """Crea y devuelve una conexión a la base de datos PostgreSQL."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres_db"),
        database=os.environ.get("POSTGRES_DB", "RasaDB"),
        user=os.environ.get("POSTGRES_USER", "postgre"),
        password=os.environ.get("POSTGRES_PASSWORD", "RasaChatBot_2026")
    )


# ID de la asignatura activa. En el futuro se obtendrá del contexto de la conversación.
ASIGNATURA_ID_ACTIVA = 1


def _tema_num_from_slot(tema_slot: str) -> int | None:
    """Extrae el número de tema del valor del slot (ej: 'tema2' -> 2)."""
    if not tema_slot:
        return None
    match = re.search(r'\d+', tema_slot)
    return int(match.group()) if match else None


def load_preguntas(cuestionario_id_slot: str) -> list:
    """
    Carga las preguntas y respuestas del cuestionario desde la BBDD usando su ID.
    Devuelve una lista de dicts.
    """
    if not cuestionario_id_slot:
        return []

    preguntas_dict = {}
    try:
        cuest_id = int(cuestionario_id_slot)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT p.id, p.pregunta_texto, p.imagen_url, r.texto_opcion, r.es_correcta, r.feedback
                    FROM CUESTIONARIOS_PREGUNTAS p
                    JOIN CUESTIONARIOS_RESPUESTAS r ON r.pregunta_id = p.id
                    WHERE p.cuestionario_id = %s
                    ORDER BY p.id ASC, r.id ASC
                """
                cur.execute(query, (cuest_id,))
                rows = cur.fetchall()
        for row in rows:
            p_id = str(row[0])
            if p_id not in preguntas_dict:
                preguntas_dict[p_id] = {
                    "id": p_id,
                    "pregunta_base": row[1],
                    "imagen_url": row[2],
                    "opciones": [],
                    "correcta": "",
                    "feedback_acierto": "¡Acertada!",
                    "feedback_fallo": "Fallaste.",
                }
            preguntas_dict[p_id]["opciones"].append(row[3])
            if row[4]:  # es_correcta
                match = re.match(r'^[A-Z]\d*', row[3])
                preguntas_dict[p_id]["correcta"] = match.group() if match else row[3]
                if row[5]:
                    try:
                        fb = json.loads(row[5])
                        preguntas_dict[p_id]["feedback_acierto"] = fb.get("acierto", "¡Acertada!")
                        preguntas_dict[p_id]["feedback_fallo"] = fb.get("fallo", "Fallaste.")
                    except (json.JSONDecodeError, TypeError):
                        pass
    except Exception as e:
        print(f"[load_preguntas] Error: {e}")

    preguntas = []
    for p_data in preguntas_dict.values():
        full_q = p_data["pregunta_base"]
        if p_data["opciones"]:
            full_q += "\n\n  " + "\n  ".join(p_data["opciones"])
        preguntas.append({
            "id": p_data["id"],
            "pregunta": full_q,
            "imagen_url": p_data["imagen_url"],
            "correcta": p_data["correcta"],
            "feedback_acierto": p_data["feedback_acierto"],
            "feedback_fallo": p_data["feedback_fallo"],
        })
    return preguntas


def load_conceptos(tema_slot: str) -> list:
    """
    Carga los conceptos teóricos de un tema desde la BBDD.
    Devuelve una lista de dicts con claves: id, termino, termino_legible, definicion.
    """
    tema_num = _tema_num_from_slot(tema_slot)
    if tema_num is None:
        return []

    conceptos = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT ct.id, ct.termino, ct.termino_legible, ct.definicion
                    FROM CONCEPTOS_TEORICOS ct
                    JOIN TEMAS t ON ct.tema_id = t.id
                    WHERE t.numero = %s AND t.asignatura_id = %s
                    ORDER BY ct.id ASC
                """
                cur.execute(query, (tema_num, ASIGNATURA_ID_ACTIVA))
                rows = cur.fetchall()
        for row in rows:
            conceptos.append({
                "id": str(row[0]),
                "termino": row[1],
                "termino_legible": row[2] if row[2] else row[1].replace("_", " ").title(),
                "definicion": row[3],
            })
    except Exception as e:
        print(f"[load_conceptos] Error: {e}")
    return conceptos


def load_todos_los_temas() -> list:
    """
    Carga todos los temas registrados en la BBDD.
    Devuelve una lista de números de tema (int).
    """
    temas = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT numero FROM TEMAS WHERE asignatura_id = %s ORDER BY numero ASC",
                    (ASIGNATURA_ID_ACTIVA,)
                )
                temas = [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"[load_todos_los_temas] Error: {e}")
    return temas


# ---------------------------------------------------------------------------
# Helpers de escritura en BBDD
# ---------------------------------------------------------------------------

def guardar_interaccion(alumno_id: str, tipo_consulta: str, mensaje: str) -> None:
    """
    Registra una interacción del alumno en INTERACCIONES_CHAT.
    alumno_id puede ser None cuando el alumno aún no está registrado;
    en ese caso se guarda NULL (la FK admite SET NULL).
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Verificar que el alumno_id exista en ALUMNOS; si no, guardar NULL
                if alumno_id:
                    cur.execute("SELECT 1 FROM ALUMNOS WHERE rasa_sender_id = %s", (alumno_id,))
                    if not cur.fetchone():
                        alumno_id = None
                cur.execute(
                    """
                    INSERT INTO INTERACCIONES_CHAT (alumno_id, tipo_consulta, mensaje_usuario)
                    VALUES (%s, %s, %s)
                    """,
                    (alumno_id, tipo_consulta, mensaje)
                )
    except Exception as e:
        print(f"[guardar_interaccion] Error: {e}")


def esta_matriculado(alumno_id: str, asignatura_id: int) -> bool:
    """Devuelve True si el alumno tiene matrícula activa en la asignatura indicada."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM MATRICULAS
                    WHERE alumno_id = %s AND asignatura_id = %s
                    """,
                    (alumno_id, asignatura_id)
                )
                return cur.fetchone() is not None
    except Exception as e:
        print(f"[esta_matriculado] Error: {e}")
        return False


def iniciar_seguimiento(alumno_id: str, cuestionario_id: int) -> int | None:
    """
    Crea una fila en SEGUIMIENTO y devuelve su id.
    Si ya existe una sesión previa para el mismo alumno y cuestionario,
    crea igualmente una nueva (permite reintentos).
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO SEGUIMIENTO (alumno_id, cuestionario_id)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (alumno_id, cuestionario_id)
                )
                return cur.fetchone()[0]
    except Exception as e:
        print(f"[iniciar_seguimiento] Error: {e}")
        return None


def guardar_detalle_respuesta(seguimiento_id: int, pregunta_id: int, respuesta_id: int) -> None:
    """Registra la respuesta elegida para una pregunta en SEGUIMIENTO_DETALLE."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO SEGUIMIENTO_DETALLE (seguimiento_id, pregunta_id, respuesta_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (seguimiento_id, pregunta_id) DO UPDATE
                        SET respuesta_id = EXCLUDED.respuesta_id
                    """,
                    (seguimiento_id, pregunta_id, respuesta_id)
                )
    except Exception as e:
        print(f"[guardar_detalle_respuesta] Error: {e}")


def actualizar_puntuacion(seguimiento_id: int, puntuacion: float) -> None:
    """Actualiza la puntuación total en SEGUIMIENTO al finalizar el cuestionario."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE SEGUIMIENTO SET puntuacion_total = %s WHERE id = %s",
                    (puntuacion, seguimiento_id)
                )
    except Exception as e:
        print(f"[actualizar_puntuacion] Error: {e}")


def get_cuestionario_id(tema_num: int, asignatura_id: int) -> int | None:
    """Devuelve el id del cuestionario de un tema dado."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.id FROM CUESTIONARIOS c
                    JOIN TEMAS t ON c.tema_id = t.id
                    WHERE t.numero = %s AND t.asignatura_id = %s
                    LIMIT 1
                    """,
                    (tema_num, asignatura_id)
                )
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        print(f"[get_cuestionario_id] Error: {e}")
        return None


def get_respuesta_id_elegida(pregunta_id: int, texto_respuesta: str) -> int | None:
    """
    Dado el id de la pregunta y el texto de la respuesta (o su letra inicial),
    intenta localizar el id de la opción más probable en CUESTIONARIOS_RESPUESTAS.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                texto_limpio = texto_respuesta.strip().upper()
                letra = texto_limpio[0] if texto_limpio else None
                # Primero intenta match exacto o casi exacto
                cur.execute(
                    """
                    SELECT id FROM CUESTIONARIOS_RESPUESTAS
                    WHERE pregunta_id = %s AND UPPER(texto_opcion) LIKE %s
                    LIMIT 1
                    """,
                    (pregunta_id, f"%{texto_limpio}%")
                )
                row = cur.fetchone()
                
                # Si no encuentra, busca por la primera letra (A, B, C...)
                if not row and letra:
                    cur.execute(
                        """
                        SELECT id FROM CUESTIONARIOS_RESPUESTAS
                        WHERE pregunta_id = %s AND UPPER(texto_opcion) LIKE %s
                        LIMIT 1
                        """,
                        (pregunta_id, f"{letra}%")
                    )
                    row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        print(f"[get_respuesta_id_elegida] Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Helpers de lectura: progreso del alumno
# ---------------------------------------------------------------------------

def get_progreso_alumno(alumno_id: str) -> dict:
    """
    Agrega en la BBDD todas las métricas de progreso del alumno y las
    devuelve en un dict con la siguiente estructura:

            {
              "dias_activo":           int,
              "total_interacciones":   int,
              "conceptos_consultados": int,
              "por_tema": [
              {"tema_num": int, "tema_titulo": str,
               "intentos": int, "media": float, "mejor": float},
              ...
              ],
              "media_global": float | None,
            }

    Si no existe ningún dato devuelve la estructura con valores a 0 / [].
    """
    resultado = {
            "dias_activo": 0,
            "total_interacciones": 0,
            "conceptos_consultados": 0,
            "por_tema": [],
            "media_global": None,
    }
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # ── 1. Actividad general desde INTERACCIONES_CHAT ──────────────────
                cur.execute(
                    """
                    SELECT
                        COUNT(DISTINCT fecha::date) AS dias_activo,
                        COUNT(*)                    AS total_interacciones,
                        COUNT(*) FILTER (WHERE tipo_consulta = 'consultar_concepto')
                                                    AS conceptos_consultados
                    FROM INTERACCIONES_CHAT
                    WHERE alumno_id = %s
                    """,
                    (alumno_id,)
                )
                row = cur.fetchone()
                if row:
                    resultado["dias_activo"]           = row[0] or 0
                    resultado["total_interacciones"]   = row[1] or 0
                    resultado["conceptos_consultados"] = row[2] or 0

                # ── 2. Resultados por tema desde SEGUIMIENTO ───────────────────────
                cur.execute(
                    """
                    SELECT
                        t.numero                                        AS tema_num,
                        t.titulo                                        AS tema_titulo,
                        COUNT(s.id)                                     AS intentos,
                        ROUND(AVG(s.puntuacion_total)::numeric, 2)      AS media,
                        MAX(s.puntuacion_total)                         AS mejor
                    FROM SEGUIMIENTO s
                    JOIN CUESTIONARIOS c ON s.cuestionario_id = c.id
                    JOIN TEMAS t         ON c.tema_id = t.id
                    WHERE s.alumno_id = %s
                      AND s.puntuacion_total IS NOT NULL
                    GROUP BY t.numero, t.titulo
                    ORDER BY t.numero ASC
                    """,
                    (alumno_id,)
                )
                filas = cur.fetchall()
                resultado["por_tema"] = [
                    {
                        "tema_num":    f[0],
                        "tema_titulo": f[1],
                        "intentos":    f[2],
                        "media":       float(f[3]) if f[3] is not None else 0.0,
                        "mejor":       float(f[4]) if f[4] is not None else 0.0,
                    }
                    for f in filas
                ]

                # ── 3. Media global ────────────────────────────────────────────────
                if resultado["por_tema"]:
                    cur.execute(
                        """
                        SELECT ROUND(AVG(puntuacion_total)::numeric, 2)
                        FROM SEGUIMIENTO
                        WHERE alumno_id = %s AND puntuacion_total IS NOT NULL
                        """,
                        (alumno_id,)
                    )
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        resultado["media_global"] = float(row[0])

    except Exception as e:
        print(f"[get_progreso_alumno] Error: {e}")
    return resultado


# ---------------------------------------------------------------------------
# Acciones de registro de intenciones (log universal)
# ---------------------------------------------------------------------------

class ActionRegistrarIntent(Action):
    """
    Registra en INTERACCIONES_CHAT el intent detectado por Rasa para cada
    mensaje del usuario. Se invoca desde rules.yml y stories.yml antes de
    las acciones principales, de modo que queda trazabilidad de TODAS las
    intenciones reconocidas (incluso las que solo disparan utter_*).

    El campo tipo_consulta almacena: 'intent:<nombre> (conf=X.XX)'.
    El campo mensaje_usuario almacena el texto original del usuario.
    """
    def name(self) -> Text:
        return "action_registrar_intent"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_data   = tracker.latest_message.get("intent", {})
        intent_name   = intent_data.get("name") or "desconocido"
        confidence    = intent_data.get("confidence", 0.0)
        texto_usuario = tracker.latest_message.get("text", "") or ""
        guardar_interaccion(
            alumno_id=tracker.sender_id,
            tipo_consulta=f"intent:{intent_name} (conf={confidence:.2f})",
            mensaje=texto_usuario
        )
        return []


class ActionDefaultFallback(Action):
    """
    Sobrescribe action_default_fallback para que los mensajes que no superan
    el umbral de confianza del NLU queden registrados en INTERACCIONES_CHAT
    con tipo_consulta = 'intent:no_detectado'.

    El campo mensaje_usuario guarda el texto íntegro del alumno para que
    el profesor pueda revisar qué preguntas no cubre el bot actualmente.
    """
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_data   = tracker.latest_message.get("intent", {})
        intent_name   = intent_data.get("name") or "nlu_fallback"
        confidence    = intent_data.get("confidence", 0.0)
        texto_usuario = tracker.latest_message.get("text", "") or ""

        # Registrar como intención NO detectada; el mensaje incluye metadatos
        # del NLU para facilitar el análisis posterior.
        guardar_interaccion(
            alumno_id=tracker.sender_id,
            tipo_consulta="intent:no_detectado",
            mensaje=f"[intent_sugerido={intent_name}, conf={confidence:.2f}] {texto_usuario}"
        )

        dispatcher.utter_message(
            text="Lo siento, no he entendido tu mensaje. Puedes preguntarme sobre horarios, "
                 "profesorado, entregas, conceptos teóricos o cuestionarios de repaso."
        )
        return [UserUtteranceReverted()]


# ---------------------------------------------------------------------------
# Acciones de consulta de horarios y tutorías (Dinámicas)
# ---------------------------------------------------------------------------

class ActionMostrarHorario(Action):
    def name(self) -> Text:
        return "action_mostrar_horario"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent_name = tracker.latest_message.get("intent", {}).get("name")
        dia_semana = intent_name if intent_name in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'] else None
        
        if not dia_semana:
            dispatcher.utter_message(text="No se ha especificado un día de la semana válido para buscar el horario.")
            return []

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT hora_inicio, hora_fin, aula, grupo 
                        FROM CLASE_HORARIO 
                        WHERE dia_semana = %s AND asignatura_id = %s
                        ORDER BY hora_inicio ASC
                        """,
                        (dia_semana, ASIGNATURA_ID_ACTIVA)
                    )
                    clases = cur.fetchall()

            if clases:
                mensaje = f"Clases del {dia_semana.capitalize()}:\n"
                for hora_inicio, hora_fin, aula, grupo in clases:
                    h_ini = hora_inicio.strftime("%H:%M") if hasattr(hora_inicio, 'strftime') else hora_inicio
                    h_fin = hora_fin.strftime("%H:%M") if hasattr(hora_fin, 'strftime') else hora_fin
                    aula_texto = aula if aula else "Aula no especificada"
                    tipo = "Teoría" if grupo == 'GG1' else "Práctica" if grupo == 'GM1' else "Clase"
                    mensaje += f"- {h_ini} a {h_fin} en {aula_texto} ({tipo})\n"
                dispatcher.utter_message(text=mensaje.strip())
            else:
                dispatcher.utter_message(text=f"El {dia_semana} no hay clases programadas.")
        except Exception as e:
            print(f"[ActionMostrarHorario] Error: {e}")
            dispatcher.utter_message(text="Hubo un error al consultar los horarios en la base de datos.")

        return []


class ActionMostrarProfesoradoTutorias(Action):
    def name(self) -> Text:
        return "action_mostrar_profesorado_tutorias"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT p.id, p.nombre, p.correo 
                        FROM PROFESORES p
                        JOIN PROF_ASIG pa ON p.id = pa.profesor_id
                        WHERE pa.asignatura_id = %s
                        """,
                        (ASIGNATURA_ID_ACTIVA,)
                    )
                    profesores = cur.fetchall()

                    if not profesores:
                        dispatcher.utter_message(text="No hay profesores asignados a esta asignatura actualmente.")
                        return []

                    mensaje = ""
                    for p_id, p_nombre, p_correo in profesores:
                        mensaje += f"{p_nombre} - {p_correo}\nHorarios tutorías:\n"
                        cur.execute(
                            """
                            SELECT dia_semana, hora_inicio, hora_fin 
                            FROM TUTORIAS 
                            WHERE profesor_id = %s
                            ORDER BY dia_semana, hora_inicio ASC
                            """,
                            (p_id,)
                        )
                        tutorias = cur.fetchall()
                        if tutorias:
                            for dia, h_ini, h_fin in tutorias:
                                h_i = h_ini.strftime("%H:%M") if hasattr(h_ini, 'strftime') else h_ini
                                h_f = h_fin.strftime("%H:%M") if hasattr(h_fin, 'strftime') else h_fin
                                mensaje += f"  - {dia.capitalize()} {h_i} - {h_f}\n"
                        else:
                            mensaje += "  - No hay tutorías registradas.\n"
                        mensaje += "\n"
                    
                    dispatcher.utter_message(text=mensaje.strip())
        except Exception as e:
            print(f"[ActionMostrarProfesoradoTutorias] Error: {e}")
            dispatcher.utter_message(text="Hubo un error al consultar el profesorado y sus tutorías.")

        return []


# ---------------------------------------------------------------------------
# Acciones de registro de alumno y matrícula
# ---------------------------------------------------------------------------

class ActionCheckMatricula(Action):
    """
    Comprueba si el alumno está matriculado en la asignatura activa (ASIGNATURA_ID_ACTIVA).
    Establece el slot 'matriculado' con True/False.
    Las acciones de contenido (listar_temas, listar_conceptos, cuestionarios) deben
    llamarse tras esta acción y comprobar el slot antes de mostrar información.
    """
    def name(self) -> Text:
        return "action_check_matricula"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        matriculado = esta_matriculado(sender_id, ASIGNATURA_ID_ACTIVA)
        return [SlotSet("matriculado", matriculado)]


# ---------------------------------------------------------------------------
# Acciones de registro de alumno
# ---------------------------------------------------------------------------

class ActionCheckRegistro(Action):
    def name(self) -> Text:
        return "action_check_registro"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nombre FROM ALUMNOS WHERE rasa_sender_id = %s", (sender_id,))
                    alumno = cur.fetchone()
                    if alumno:
                        return [SlotSet("requiere_registro", False), SlotSet("nombre", alumno[0])]
        except Exception as e:
            print(f"[ActionCheckRegistro] Error: {e}")
        return [SlotSet("requiere_registro", True)]


class ActionGuardarAlumno(Action):
    def name(self) -> Text:
        return "action_guardar_alumno"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        nombre = tracker.get_slot("nombre")
        correo = tracker.get_slot("correo")
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO ALUMNOS (rasa_sender_id, nombre, correo) VALUES (%s, %s, %s) ON CONFLICT (rasa_sender_id) DO NOTHING",
                        (sender_id, nombre, correo)
                    )
        except Exception as e:
            print(f"[ActionGuardarAlumno] Error: {e}")
        return [SlotSet("requiere_registro", False)]


class ValidateRegistroForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_registro_form"

    def validate_correo(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        correo = str(slot_value).strip().lower()
        if correo.endswith("@uco.es"):
            return {"correo": correo}
        dispatcher.utter_message(text="El correo debe ser una dirección válida de la Universidad de Córdoba (terminada en @uco.es). Por favor, introdúzcalo de nuevo.")
        return {"correo": None}


# ---------------------------------------------------------------------------
# Acción: listar temas (unificada para conceptos y cuestionarios)
# ---------------------------------------------------------------------------

class ActionListarTemas(Action):
    def name(self) -> Text:
        return "action_listar_temas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Bloquear si el alumno no está matriculado en la asignatura activa
        if not esta_matriculado(tracker.sender_id, ASIGNATURA_ID_ACTIVA):
            dispatcher.utter_message(
                text="⚠️ No estás matriculado en la asignatura de Redes. "
                     "Contacta con la administración si crees que es un error."
            )
            return []

        temas = load_todos_los_temas()

        if not temas:
            dispatcher.utter_message(text="Actualmente no hay temas registrados en el sistema.")
            return []

        buttons = [
            {
                "title": f"Tema {num}",
                "payload": f'/seleccionar_tema{{"tema_actual":"tema{num}"}}'
            }
            for num in temas
        ]
        dispatcher.utter_message(text="¿Qué tema deseas repasar?", buttons=buttons)
        return []


# ---------------------------------------------------------------------------
# Acciones: conceptos teóricos dinámicos
# ---------------------------------------------------------------------------

class ActionListarConceptos(Action):
    """
    Muestra los conceptos teóricos disponibles para el tema seleccionado.
    Si no hay conceptos, informa al usuario.
    Requiere que el alumno esté matriculado en la asignatura activa.
    """
    def name(self) -> Text:
        return "action_listar_conceptos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Bloquear si el alumno no está matriculado
        if not esta_matriculado(tracker.sender_id, ASIGNATURA_ID_ACTIVA):
            dispatcher.utter_message(
                text="⚠️ No estás matriculado en la asignatura de Redes. "
                     "No puedes acceder al contenido de esta asignatura."
            )
            return []

        tema = tracker.get_slot("tema_actual")
        tema_num = _tema_num_from_slot(tema)
        conceptos = load_conceptos(tema)

        guardar_interaccion(
            alumno_id=tracker.sender_id,
            tipo_consulta="listar_conceptos",
            mensaje=f"Tema {tema_num}"
        )

        if not conceptos:
            dispatcher.utter_message(
                text=f"Actualmente no hay conceptos teóricos del Tema {tema_num} en la base de datos."
            )
            return []

        buttons = [
            {
                "title": c["termino_legible"],
                "payload": f'/seleccionar_concepto{{"concepto_id":"{c["id"]}"}}'
            }
            for c in conceptos
        ]
        dispatcher.utter_message(
            text=f"Estos son los conceptos del Tema {tema_num}. Selecciona el que quieres consultar:",
            buttons=buttons
        )
        return []


class ActionDarConcepto(Action):
    """
    Muestra la definición del concepto seleccionado, leyendo su ID desde el slot.
    """
    def name(self) -> Text:
        return "action_dar_concepto"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Bloquear si el alumno no está matriculado
        if not esta_matriculado(tracker.sender_id, ASIGNATURA_ID_ACTIVA):
            dispatcher.utter_message(
                text="⚠️ No estás matriculado en la asignatura de Redes. "
                     "No puedes acceder a las definiciones de esta asignatura."
            )
            return []

        concepto_id = tracker.get_slot("concepto_id")

        if not concepto_id:
            dispatcher.utter_message(text="No se ha seleccionado ningún concepto.")
            return []

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT termino_legible, definicion FROM CONCEPTOS_TEORICOS WHERE id = %s",
                        (concepto_id,)
                    )
                    row = cur.fetchone()

            if row:
                termino_legible, definicion = row
                # Registrar interacción
                guardar_interaccion(
                    alumno_id=tracker.sender_id,
                    tipo_consulta="consultar_concepto",
                    mensaje=termino_legible
                )
                dispatcher.utter_message(text=f"**{termino_legible}**\n\n{definicion}")
            else:
                dispatcher.utter_message(text="No se ha encontrado la definición para este concepto.")
        except Exception as e:
            print(f"[ActionDarConcepto] Error: {e}")
            dispatcher.utter_message(text="Hubo un error al buscar el concepto en la base de datos.")

        return []


# ---------------------------------------------------------------------------
# Acciones: cuestionarios dinámicos
# ---------------------------------------------------------------------------

class ActionListarCuestionarios(Action):
    def name(self) -> Text:
        return "action_listar_cuestionarios"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not esta_matriculado(tracker.sender_id, ASIGNATURA_ID_ACTIVA):
            dispatcher.utter_message(text="⚠️ No estás matriculado en la asignatura de Redes.")
            return []

        tema = tracker.get_slot("tema_actual")
        tema_num = _tema_num_from_slot(tema)
        tipo = tracker.get_slot("tipo_cuestionario") or "teoria"

        cuestionarios = []
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT c.id, c.titulo 
                        FROM CUESTIONARIOS c
                        JOIN TEMAS t ON c.tema_id = t.id
                        WHERE t.numero = %s AND t.asignatura_id = %s AND c.tipo = %s
                        ORDER BY c.id ASC
                        """,
                        (tema_num, ASIGNATURA_ID_ACTIVA, tipo)
                    )
                    cuestionarios = cur.fetchall()
        except Exception as e:
            print(f"[ActionListarCuestionarios] Error: {e}")

        tipo_txt = "cuestionarios de teoría" if tipo == "teoria" else "ejercicios prácticos"

        if not cuestionarios:
            dispatcher.utter_message(text=f"No hay {tipo_txt} disponibles en la base de datos para el Tema {tema_num}.")
            return []

        if len(cuestionarios) == 1:
            cuest_id = str(cuestionarios[0][0])
            return [
                SlotSet("cuestionario_id_seleccionado", cuest_id),
                FollowupAction("action_reset_cuestionario_dinamico")
            ]

        buttons = [
            {
                "title": titulo,
                "payload": f'/seleccionar_cuestionario{{"cuestionario_id_seleccionado":"{c_id}"}}'
            }
            for c_id, titulo in cuestionarios
        ]
        dispatcher.utter_message(text=f"Hay varios {tipo_txt} para el Tema {tema_num}. Elige uno:", buttons=buttons)
        return []


class ActionResetCuestionarioDinamico(Action):
    def name(self) -> Text:
        return "action_reset_cuestionario_dinamico"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Bloquear si el alumno no está matriculado
        if not esta_matriculado(tracker.sender_id, ASIGNATURA_ID_ACTIVA):
            dispatcher.utter_message(
                text="⚠️ No estás matriculado en la asignatura de Redes. "
                     "No puedes acceder a los cuestionarios de esta asignatura."
            )
            return [
                SlotSet("pregunta_actual_idx", 0),
                SlotSet("respuesta_generica", None),
                SlotSet("seguimiento_id", None),
                SlotSet("aciertos_cuestionario", 0),
            ]

        cuest_id = tracker.get_slot("cuestionario_id_seleccionado")
        if not cuest_id:
            dispatcher.utter_message(text="No se ha seleccionado ningún cuestionario.")
            return []

        preguntas = load_preguntas(cuest_id)
        seguimiento_id = None
        if preguntas:
            seguimiento_id = iniciar_seguimiento(tracker.sender_id, int(cuest_id))
            guardar_interaccion(
                alumno_id=tracker.sender_id,
                tipo_consulta="iniciar_cuestionario",
                mensaje=f"Cuestionario {cuest_id}"
            )
            dispatcher.utter_message(
                text=f"Perfecto, pues ahora realizaremos el tipo test. "
                     f"Recuerde contestar con letra y/o número (ej: A1). ¡Mucha suerte!"
            )
            dispatcher.utter_message(
                text=preguntas[0]["pregunta"],
                image=preguntas[0].get("imagen_url")
            )
        else:
            dispatcher.utter_message(
                text="El cuestionario seleccionado no tiene preguntas cargadas en la base de datos."
            )

        return [
            SlotSet("pregunta_actual_idx", 0),
            SlotSet("respuesta_generica", None),
            SlotSet("seguimiento_id", seguimiento_id),
            SlotSet("aciertos_cuestionario", 0),
        ]


class ActionCancelarCuestionario(Action):
    """
    Cancela un cuestionario en curso. Borra la entrada de SEGUIMIENTO de la base de datos
    para que este intento fallido no compute en las estadísticas, y limpia los slots.
    """
    def name(self) -> Text:
        return "action_cancelar_cuestionario"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        seguimiento_id = tracker.get_slot("seguimiento_id")
        tema = tracker.get_slot("tema_actual")
        tema_num = _tema_num_from_slot(tema)

        if seguimiento_id:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM SEGUIMIENTO WHERE id = %s", (seguimiento_id,))
            except Exception as e:
                print(f"[ActionCancelarCuestionario] Error al borrar seguimiento: {e}")

        guardar_interaccion(
            alumno_id=tracker.sender_id,
            tipo_consulta="cancelar_cuestionario",
            mensaje=f"Tema {tema_num} (Cancelado)"
        )

        dispatcher.utter_message(text="Cuestionario cancelado. Este intento no contará en tu progreso.")

        return [
            ActiveLoop(None),
            SlotSet("pregunta_actual_idx", 0),
            SlotSet("respuesta_generica", None),
            SlotSet("seguimiento_id", None),
            SlotSet("aciertos_cuestionario", 0),
        ]


class ActionAskRespuestaGenerica(Action):
    def name(self) -> Text:
        return "action_ask_respuesta_generica"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Acción en blanco requerida por la arquitectura de Rasa Forms.
        # La pregunta ya se emite en la validación / reseteo explícitamente.
        return []


class ValidateCuestionarioDinamicoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cuestionario_dinamico_form"

    async def required_slots(self, domain_slots: List[Text], dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Text]:
        idx = int(tracker.get_slot("pregunta_actual_idx") or 0)
        preguntas = load_preguntas(tracker.get_slot("cuestionario_id_seleccionado"))
        return ["respuesta_generica"] if idx < len(preguntas) else []

    def validate_respuesta_generica(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        idx = int(tracker.get_slot("pregunta_actual_idx") or 0)
        cuest_id = tracker.get_slot("cuestionario_id_seleccionado")
        preguntas = load_preguntas(cuest_id)
        seguimiento_id = tracker.get_slot("seguimiento_id")
        aciertos = int(tracker.get_slot("aciertos_cuestionario") or 0)

        if idx >= len(preguntas):
            return {"respuesta_generica": slot_value}

        # Si Rasa invoca la validación con None (tras el reset), esperamos al usuario.
        if slot_value is None:
            return {"respuesta_generica": None}

        user_answer = str(slot_value).strip().upper()

        # Filtro: ignorar comandos de navegación si el usuario intenta escapar usando un texto no permitido
        # Como hemos excluido salir_cuestionario del slot, si llega aquí y pone "salir" es que no lo reconoció
        # bien, pero si lo reconoció bien, no llega aquí.
        # Si pone cualquier otra cosa que no sea correcta y sea un menú, avisamos.
        ignore_words = {"CUESTIONARIO", "CUESTIONARIOS", "TEST", "REPASO", "CONCEPTOS", "EJERCICIOS", "TEMA"}
        if user_answer.startswith("/") or any(word in user_answer for word in ignore_words):
            dispatcher.utter_message(
                text="⚠️ Actualmente estás en un cuestionario. Por favor, responde a la pregunta con la letra correspondiente o escribe 'salir' para abandonarlo."
            )
            return {"respuesta_generica": None}

        pregunta = preguntas[idx]
        correcta = pregunta["correcta"].upper()
        letra_correcta = correcta[0]
        words = user_answer.split()

        is_correct = (
            correcta in words or correcta in user_answer or
            letra_correcta in words or user_answer == letra_correcta
        )

        if is_correct:
            dispatcher.utter_message(text=pregunta["feedback_acierto"])
            aciertos += 1
        else:
            dispatcher.utter_message(text=pregunta["feedback_fallo"])

        # Guardar detalle de respuesta en SEGUIMIENTO_DETALLE
        if seguimiento_id:
            pregunta_id = int(pregunta["id"])
            respuesta_id = get_respuesta_id_elegida(pregunta_id, user_answer)
            if respuesta_id:
                guardar_detalle_respuesta(seguimiento_id, pregunta_id, respuesta_id)

        new_idx = idx + 1

        if new_idx < len(preguntas):
            dispatcher.utter_message(
                text=preguntas[new_idx]["pregunta"],
                image=preguntas[new_idx].get("imagen_url")
            )
        else:
            # Cuestionario terminado: guardar puntuación final
            tema = tracker.get_slot("tema_actual")
            if seguimiento_id and len(preguntas) > 0:
                puntuacion = round((aciertos / len(preguntas)) * 10, 2)
                actualizar_puntuacion(seguimiento_id, puntuacion)
            guardar_interaccion(
                alumno_id=tracker.sender_id,
                tipo_consulta="finalizar_cuestionario",
                mensaje=f"Tema {tema} – {aciertos}/{len(preguntas)} correctas"
            )

        return {
            "respuesta_generica": None,
            "pregunta_actual_idx": new_idx,
            "aciertos_cuestionario": aciertos,
        }


# ---------------------------------------------------------------------------
# Módulo 3: Seguimiento del progreso del estudiante
# ---------------------------------------------------------------------------

class ActionMostrarProgreso(Action):
    """
    Consulta las métricas de progreso del alumno desde la BBDD y las
    formatea en un mensaje estructurado con emojis.

    Métricas incluidas:
      - Días de actividad distintos (desde INTERACCIONES_CHAT)
      - Total de interacciones y conceptos consultados
      - Por cada tema: nº de intentos, mejor nota y nota media
      - Nota media global de todos los cuestionarios completados
    """
    def name(self) -> Text:
        return "action_mostrar_progreso"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id

        # Obtener nombre del alumno si está disponible
        nombre_slot = tracker.get_slot("nombre")
        saludo = f", {nombre_slot}" if nombre_slot else ""

        # Consultar métricas agregadas
        progreso = get_progreso_alumno(sender_id)

        # Registrar que el alumno consultó su progreso
        guardar_interaccion(
            alumno_id=sender_id,
            tipo_consulta="ver_progreso",
            mensaje="consulta de progreso"
        )

        # Caso: el alumno aún no ha completado ningún cuestionario
        if not progreso["por_tema"]:
            dispatcher.utter_message(
                text=(
                    f"📊 Tu progreso en Redes{saludo}:\n\n"
                    f"🗓️ Días activo: {progreso['dias_activo']}\n"
                    f"💬 Interacciones: {progreso['total_interacciones']}\n"
                    f"📚 Conceptos consultados: {progreso['conceptos_consultados']}\n\n"
                    "📝 Aún no has completado ningún cuestionario.\n"
                    "¡Empieza uno escribiendo 'quiero repasar'! 💪"
                )
            )
            return []

        # Construir bloque de resultados por tema
        lineas_temas = []
        for t in progreso["por_tema"]:
            intentos_str = "1 intento" if t["intentos"] == 1 else f"{t['intentos']} intentos"
            lineas_temas.append(
                f"  • Tema {t['tema_num']} — "
                f"{intentos_str} | "
                f"Mejor nota: {t['mejor']:.1f} | "
                f"Media: {t['media']:.1f}"
            )
        temas_texto = "\n".join(lineas_temas)

        media_global_texto = (
            f"🏆 Nota media global: {progreso['media_global']:.2f} / 10"
            if progreso["media_global"] is not None
            else ""
        )

        mensaje = (
            f"📊 Tu progreso en Redes{saludo}:\n\n"
            f"🗓️ Días activo: {progreso['dias_activo']}\n"
            f"💬 Interacciones totales: {progreso['total_interacciones']}\n"
            f"📚 Conceptos consultados: {progreso['conceptos_consultados']}\n\n"
            f"📝 Cuestionarios realizados:\n{temas_texto}\n\n"
            f"{media_global_texto}"
        ).strip()

        dispatcher.utter_message(text=mensaje)
        return []

# ---------------------------------------------------------------------------
# Módulo 4: Recomendaciones (MLP)
# ---------------------------------------------------------------------------

class ActionRecomendar(Action):
    def name(self) -> Text:
        return "action_recomendar"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        
        # Bloquear si el alumno no está matriculado
        if not esta_matriculado(sender_id, ASIGNATURA_ID_ACTIVA):
            dispatcher.utter_message(
                text="⚠️ No estás matriculado en la asignatura de Redes. "
                     "No puedo ofrecerte recomendaciones de estudio."
            )
            return []

        # Obtener progreso
        progreso = get_progreso_alumno(sender_id)
        
        dias_activo = progreso.get("dias_activo", 0)
        interacciones = progreso.get("total_interacciones", 0)
        conceptos_consultados = progreso.get("conceptos_consultados", 0)
        
        # Preparar array de indicadores y notas de los 6 temas
        NUM_TEMAS = 6
        indicadores = [0] * NUM_TEMAS
        notas = [0.0] * NUM_TEMAS
        
        for t in progreso.get("por_tema", []):
            idx = t["tema_num"] - 1 # temas son 1-indexados
            if 0 <= idx < NUM_TEMAS:
                indicadores[idx] = 1
                notas[idx] = t["mejor"]
                
        # Construir vector de características
        features = [dias_activo, interacciones, conceptos_consultados] + indicadores + notas
        
        try:
            # Cargar modelo MLP
            model_path = os.path.join("models", "recommender_mlp.pkl")
            if not os.path.exists(model_path):
                dispatcher.utter_message(text="El modelo de recomendaciones no está disponible actualmente.")
                return []
                
            clf = joblib.load(model_path)
            
            # Predecir
            X = np.array([features])
            prediction = clf.predict(X)[0]
            
            # Interpretar predicción y devolver respuesta
            if prediction.startswith("repasar_tema_"):
                tema_num = prediction.split("_")[-1]
                botones = [{"title": f"Repasar Tema {tema_num}", "payload": f'/seleccionar_tema{{"tema_actual":"tema{tema_num}"}}'}]
                
                dispatcher.utter_message(
                    text=f"🤖 **Recomendación de la IA:** He analizado tu progreso y veo que necesitas reforzar el **Tema {tema_num}**. "
                         "Te sugiero repasar sus conceptos y volver a intentar el cuestionario para mejorar tus resultados.",
                    buttons=botones
                )
            elif prediction == "avanzar_siguiente_tema":
                # Buscar el primer tema que no ha intentado
                tema_siguiente = 1
                for i, ind in enumerate(indicadores):
                    if ind == 0:
                        tema_siguiente = i + 1
                        break
                        
                botones = [{"title": f"Ir al Tema {tema_siguiente}", "payload": f'/seleccionar_tema{{"tema_actual":"tema{tema_siguiente}"}}'}]
                dispatcher.utter_message(
                    text=f"🤖 **Recomendación de la IA:** ¡Vas muy bien! Tus notas son buenas. "
                         f"Te recomiendo avanzar hacia el **Tema {tema_siguiente}**.",
                    buttons=botones
                )
            elif prediction == "hacer_examen_global":
                dispatcher.utter_message(
                    text="🤖 **Recomendación de la IA:** ¡Excelente trabajo! Has completado y dominado todos los temas. "
                         "¡Estás preparado/a para el examen final!"
                )
            else:
                dispatcher.utter_message(text="🤖 No estoy seguro de qué recomendarte en este momento. ¡Sigue estudiando!")
                
        except Exception as e:
            print(f"[ActionRecomendar] Error: {e}")
            dispatcher.utter_message(text="Ha ocurrido un error al generar la recomendación.")

        return []
