from typing import Any, Text, Dict, List
from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
import json
import os
import re

def load_preguntas(tema_id):
    if not tema_id:
        return []
    path = os.path.join(os.path.dirname(__file__), "..", "data", f"preguntas_{tema_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

class ActionListarTemas(Action):
    def name(self) -> Text:
        return "action_listar_temas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        path = os.path.join(os.path.dirname(__file__), "..", "data")
        temas_disponibles = []
        pattern = re.compile(r"^preguntas_(tema\d+|t\d+)\.json$")
        
        if os.path.exists(path):
            for filename in os.listdir(path):
                match = pattern.match(filename)
                if match:
                    tema_id = match.group(1)
                    num = ''.join(filter(str.isdigit, tema_id))
                    temas_disponibles.append({
                        "title": f"Tema {num}",
                        "payload": f'/seleccionar_tema{{"tema_actual":"{tema_id}"}}'
                    })
                    
        if temas_disponibles:
            temas_disponibles.sort(key=lambda x: int(''.join(filter(str.isdigit, x["title"]))))
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
