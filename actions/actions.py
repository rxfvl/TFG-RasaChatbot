from typing import Any, Text, Dict, List
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
import json
import os
import re
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres_db"),
        database=os.environ.get("POSTGRES_DB", "RasaDB"),
        user=os.environ.get("POSTGRES_USER", "postgre"),
        password=os.environ.get("POSTGRES_PASSWORD", "RasaChatBot_2026")
    )

def load_preguntas(tema_id):
    if not tema_id:
        return []
    
    num_match = re.search(r'\d+', tema_id)
    if not num_match:
        return []
    num = int(num_match.group())
    
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
            WHERE t.numero = %s
            ORDER BY p.id ASC, r.id ASC
        """
        cur.execute(query, (num,))
        rows = cur.fetchall()
        for row in rows:
            p_id = str(row[0])
            p_text = row[1]
            r_text = row[2]
            es_correcta = row[3]
            feedback_json_str = row[4]
            
            if p_id not in preguntas_dict:
                preguntas_dict[p_id] = {
                    "id": p_id,
                    "pregunta_base": p_text,
                    "opciones": [],
                    "correcta": "",
                    "feedback_acierto": "¡Acertada!",
                    "feedback_fallo": "Fallaste."
                }
                
            preguntas_dict[p_id]["opciones"].append(r_text)
            
            if es_correcta:
                match = re.match(r'^[A-Z]\d*', r_text)
                if match:
                    preguntas_dict[p_id]["correcta"] = match.group()
                else:
                    preguntas_dict[p_id]["correcta"] = r_text
                    
                if feedback_json_str:
                    try:
                        fb = json.loads(feedback_json_str)
                        preguntas_dict[p_id]["feedback_acierto"] = fb.get("acierto", "¡Acertada!")
                        preguntas_dict[p_id]["feedback_fallo"] = fb.get("fallo", "Fallaste.")
                    except:
                        pass
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error loading questions: {e}")
        
    preguntas = []
    for p_id, p_data in preguntas_dict.items():
        full_q = p_data["pregunta_base"]
        if p_data["opciones"]:
            full_q += "\n\n  " + "\n  ".join(p_data["opciones"])
            
        preguntas.append({
            "id": p_id,
            "pregunta": full_q,
            "correcta": p_data["correcta"],
            "feedback_acierto": p_data["feedback_acierto"],
            "feedback_fallo": p_data["feedback_fallo"]
        })
        
    return preguntas

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
            else:
                return [SlotSet("requiere_registro", True)]
        except Exception as e:
            print(f"Error checking registration: {e}")
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
            print(f"Error saving registration: {e}")
            
        return [SlotSet("requiere_registro", False)]

class ValidateRegistroForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_registro_form"

    def validate_correo(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        correo = str(slot_value).strip().lower()
        if correo.endswith("@uco.es"):
            return {"correo": correo}
        else:
            dispatcher.utter_message(text="El correo debe ser una dirección válida de la Universidad de Córdoba (terminada en @uco.es). Por favor, introdúzcalo de nuevo.")
            return {"correo": None}

class ActionListarTemas(Action):
    def name(self) -> Text:
        return "action_listar_temas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        temas_disponibles = []
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Buscamos los temas que tengan un cuestionario asociado
            query = """
                SELECT DISTINCT t.numero 
                FROM TEMAS t
                JOIN CUESTIONARIOS c ON c.tema_id = t.id
                ORDER BY t.numero ASC
            """
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                num = row[0]
                temas_disponibles.append({
                    "title": f"Tema {num}",
                    "payload": f'/seleccionar_tema{{"tema_actual":"tema{num}"}}'
                })
                
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching temas: {e}")
            
        if temas_disponibles:
            dispatcher.utter_message(text="¿Qué tema deseas repasar?", buttons=temas_disponibles)
        else:
            dispatcher.utter_message(text="Actualmente no hay cuestionarios disponibles registrados.")
            
        return []

class ActionResetCuestionarioDinamico(Action):
    def name(self) -> Text:
        return "action_reset_cuestionario_dinamico"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Lanzamos la primera pregunta directamente al arrancar, evitando bugs de Rasa
        tema = tracker.get_slot("tema_actual")
        preguntas = load_preguntas(tema)
        
        if len(preguntas) > 0:
            num = ''.join(filter(str.isdigit, tema)) if tema else ""
            dispatcher.utter_message(text=f"Perfecto, pues ahora realizaremos un tipo test del Tema {num}. Recuerde contestar con letra y/o número (ej: A1). ¡Mucha suerte!")
            dispatcher.utter_message(text=preguntas[0]["pregunta"])
        else:
            dispatcher.utter_message(text="El cuestionario para este tema todavía no ha sido subido.")
            
        return [
            SlotSet("pregunta_actual_idx", 0),
            SlotSet("respuesta_generica", None)
        ]

class ActionAskRespuestaGenerica(Action):
    def name(self) -> Text:
        return "action_ask_respuesta_generica"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Acción en blanco requerida por la arquitectura de Rasa Forms
        # La pregunta ya la arrojamos en la validación / reseteo explícitamente
        return []

class ValidateCuestionarioDinamicoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cuestionario_dinamico_form"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        idx = int(tracker.get_slot("pregunta_actual_idx") or 0)
        tema = tracker.get_slot("tema_actual")
        preguntas = load_preguntas(tema)
        
        if idx < len(preguntas):
            return ["respuesta_generica"]
        else:
            return []

    def validate_respuesta_generica(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        idx = int(tracker.get_slot("pregunta_actual_idx") or 0)
        tema = tracker.get_slot("tema_actual")
        preguntas = load_preguntas(tema)
        
        if idx >= len(preguntas):
            return {"respuesta_generica": slot_value}

        # Bicho detectado: si `action_reset` establece el slot a None para limpiarlo, 
        # Rasa invoca esta validación con slot_value = None. 
        # No debemos evaluar 'None', sino forzar la espera del usuario.
        if slot_value is None:
            return {"respuesta_generica": None}

        user_answer = str(slot_value).strip().upper()
        
        # Superfiltro: Si el texto capturado es evidentemente un comando, botón del menú u otra frase larga de navegación...
        ignore_words = ["CUESTIONARIO", "CUESTIONARIOS", "TEST", "REPASO", "CONCEPTOS", "EJERCICIOS"]
        if user_answer.startswith("/") or user_answer in ignore_words:
            # Ignorarlo limpiamente sin avanzar la pregunta
            return {"respuesta_generica": None}
            
        pregunta = preguntas[idx]
        
        correcta = pregunta["correcta"].upper()     # e.g., "A1"
        letra_correcta = correcta[0]                # e.g., "A"
        
        words = user_answer.split()
        
        is_correct = False
        if correcta in words or correcta in user_answer:
            is_correct = True
        elif letra_correcta in words or user_answer == letra_correcta:
            is_correct = True

        # Emitir feedback
        if is_correct:
            dispatcher.utter_message(text=pregunta["feedback_acierto"])
        else:
            dispatcher.utter_message(text=pregunta["feedback_fallo"])
            
        new_idx = idx + 1
        
        # Automáticamente empalmar y formular la SIGUIENTE pregunta
        if new_idx < len(preguntas):
            dispatcher.utter_message(text=preguntas[new_idx]["pregunta"])
            
        return {"respuesta_generica": None, "pregunta_actual_idx": new_idx}
