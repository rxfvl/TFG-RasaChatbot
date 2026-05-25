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
"""

from typing import Any, Text, Dict, List
import json
import os
import re
import psycopg2

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
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


def load_preguntas(tema_slot: str) -> list:
    """
    Carga las preguntas y respuestas del cuestionario de un tema desde la BBDD.
    Devuelve una lista de dicts con claves: id, pregunta, correcta,
    feedback_acierto, feedback_fallo.
    """
    tema_num = _tema_num_from_slot(tema_slot)
    if tema_num is None:
        return []

    preguntas_dict = {}
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            SELECT p.id, p.pregunta_texto, r.texto_opcion, r.es_correcta, r.feedback
            FROM TEMAS t
            JOIN CUESTIONARIOS c ON c.tema_id = t.id
            JOIN CUESTIONARIOS_PREGUNTAS p ON p.cuestionario_id = c.id
            JOIN CUESTIONARIOS_RESPUESTAS r ON r.pregunta_id = p.id
            WHERE t.numero = %s AND t.asignatura_id = %s
            ORDER BY p.id ASC, r.id ASC
        """
        cur.execute(query, (tema_num, ASIGNATURA_ID_ACTIVA))
        rows = cur.fetchall()
        for row in rows:
            p_id = str(row[0])
            if p_id not in preguntas_dict:
                preguntas_dict[p_id] = {
                    "id": p_id,
                    "pregunta_base": row[1],
                    "opciones": [],
                    "correcta": "",
                    "feedback_acierto": "¡Acertada!",
                    "feedback_fallo": "Fallaste.",
                }
            preguntas_dict[p_id]["opciones"].append(row[2])
            if row[3]:  # es_correcta
                match = re.match(r'^[A-Z]\d*', row[2])
                preguntas_dict[p_id]["correcta"] = match.group() if match else row[2]
                if row[4]:
                    try:
                        fb = json.loads(row[4])
                        preguntas_dict[p_id]["feedback_acierto"] = fb.get("acierto", "¡Acertada!")
                        preguntas_dict[p_id]["feedback_fallo"] = fb.get("fallo", "Fallaste.")
                    except (json.JSONDecodeError, TypeError):
                        pass
        cur.close()
        conn.close()
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
        conn = get_db_connection()
        cur = conn.cursor()
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
        cur.close()
        conn.close()
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
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT numero FROM TEMAS WHERE asignatura_id = %s ORDER BY numero ASC",
            (ASIGNATURA_ID_ACTIVA,)
        )
        temas = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[load_todos_los_temas] Error: {e}")
    return temas


# ---------------------------------------------------------------------------
# Acciones de registro
# ---------------------------------------------------------------------------

class ActionCheckRegistro(Action):
    def name(self) -> Text:
        return "action_check_registro"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        sender_id = tracker.sender_id
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM ALUMNOS WHERE rasa_sender_id = %s", (sender_id,))
            alumno = cur.fetchone()
            cur.close()
            conn.close()
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
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO ALUMNOS (rasa_sender_id, nombre, correo) VALUES (%s, %s, %s) ON CONFLICT (rasa_sender_id) DO NOTHING",
                (sender_id, nombre, correo)
            )
            conn.commit()
            cur.close()
            conn.close()
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
    """
    def name(self) -> Text:
        return "action_listar_conceptos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tema = tracker.get_slot("tema_actual")
        tema_num = _tema_num_from_slot(tema)
        conceptos = load_conceptos(tema)

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
        concepto_id = tracker.get_slot("concepto_id")

        if not concepto_id:
            dispatcher.utter_message(text="No se ha seleccionado ningún concepto.")
            return []

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT termino_legible, definicion FROM CONCEPTOS_TEORICOS WHERE id = %s",
                (concepto_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                termino_legible, definicion = row
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

class ActionResetCuestionarioDinamico(Action):
    def name(self) -> Text:
        return "action_reset_cuestionario_dinamico"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tema = tracker.get_slot("tema_actual")
        tema_num = _tema_num_from_slot(tema)
        preguntas = load_preguntas(tema)

        if preguntas:
            dispatcher.utter_message(
                text=f"Perfecto, pues ahora realizaremos un tipo test del Tema {tema_num}. "
                     f"Recuerde contestar con letra y/o número (ej: A1). ¡Mucha suerte!"
            )
            dispatcher.utter_message(text=preguntas[0]["pregunta"])
        else:
            dispatcher.utter_message(
                text=f"El cuestionario del Tema {tema_num} todavía no ha sido subido a la base de datos."
            )

        return [
            SlotSet("pregunta_actual_idx", 0),
            SlotSet("respuesta_generica", None),
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
        preguntas = load_preguntas(tracker.get_slot("tema_actual"))
        return ["respuesta_generica"] if idx < len(preguntas) else []

    def validate_respuesta_generica(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        idx = int(tracker.get_slot("pregunta_actual_idx") or 0)
        tema = tracker.get_slot("tema_actual")
        preguntas = load_preguntas(tema)

        if idx >= len(preguntas):
            return {"respuesta_generica": slot_value}

        # Si Rasa invoca la validación con None (tras el reset), esperamos al usuario.
        if slot_value is None:
            return {"respuesta_generica": None}

        user_answer = str(slot_value).strip().upper()

        # Filtro: ignorar comandos de navegación o botones del menú
        ignore_words = {"CUESTIONARIO", "CUESTIONARIOS", "TEST", "REPASO", "CONCEPTOS", "EJERCICIOS"}
        if user_answer.startswith("/") or user_answer in ignore_words:
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
        else:
            dispatcher.utter_message(text=pregunta["feedback_fallo"])

        new_idx = idx + 1
        if new_idx < len(preguntas):
            dispatcher.utter_message(text=preguntas[new_idx]["pregunta"])

        return {"respuesta_generica": None, "pregunta_actual_idx": new_idx}
