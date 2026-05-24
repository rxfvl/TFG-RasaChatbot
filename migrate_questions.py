import json
import os
import re
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="postgres_db",
        database="RasaDB",
        user="postgre",
        password="RasaChatBot_2026",
        port=5432
    )

def migrate():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ensure Asignatura exists
    cur.execute("SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'")
    asig_row = cur.fetchone()
    if not asig_row:
        cur.execute("INSERT INTO ASIGNATURAS (nombre, titulacion, curso, enlace_guia_docente) VALUES ('Redes', 'Ingeniería Informática', 'tercero', '') RETURNING id")
        asig_id = cur.fetchone()[0]
    else:
        asig_id = asig_row[0]
        
    data_dir = "data"
    for filename in os.listdir(data_dir):
        if filename.startswith("preguntas_tema") and filename.endswith(".json"):
            num_match = re.search(r'\d+', filename)
            if not num_match:
                continue
            tema_num = int(num_match.group())
            
            # Ensure Tema exists
            cur.execute("SELECT id FROM TEMAS WHERE asignatura_id = %s AND numero = %s", (asig_id, tema_num))
            tema_row = cur.fetchone()
            if not tema_row:
                cur.execute("INSERT INTO TEMAS (asignatura_id, numero, titulo) VALUES (%s, %s, %s) RETURNING id", (asig_id, tema_num, f"Tema {tema_num}"))
                tema_id = cur.fetchone()[0]
            else:
                tema_id = tema_row[0]
                
            # Ensure Cuestionario exists
            cur.execute("SELECT id FROM CUESTIONARIOS WHERE tema_id = %s", (tema_id,))
            cuest_row = cur.fetchone()
            if not cuest_row:
                cur.execute("INSERT INTO CUESTIONARIOS (tema_id, titulo) VALUES (%s, %s) RETURNING id", (tema_id, f"Cuestionario Tema {tema_num}"))
                cuest_id = cur.fetchone()[0]
            else:
                cuest_id = cuest_row[0]
                
            # Read JSON and insert questions
            with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
                preguntas = json.load(f)
                
            for p in preguntas:
                pregunta_texto = p.get("pregunta", "")
                correcta = p.get("correcta", "")
                feedback_fallo = p.get("feedback_fallo", "")
                feedback_acierto = p.get("feedback_acierto", "")
                
                parts = pregunta_texto.split("\n\n")
                if len(parts) >= 2:
                    q_text = parts[0].strip()
                    options = parts[1].strip().split("\n")
                else:
                    q_text = pregunta_texto
                    options = []
                    
                # Check if question already exists
                cur.execute("SELECT id FROM CUESTIONARIOS_PREGUNTAS WHERE cuestionario_id = %s AND pregunta_texto = %s", (cuest_id, q_text))
                if cur.fetchone():
                    continue # Skip duplicates
                    
                cur.execute(
                    "INSERT INTO CUESTIONARIOS_PREGUNTAS (cuestionario_id, pregunta_texto) VALUES (%s, %s) RETURNING id",
                    (cuest_id, q_text)
                )
                preg_id = cur.fetchone()[0]
                
                combined_feedback = json.dumps({
                    "acierto": feedback_acierto,
                    "fallo": feedback_fallo
                }, ensure_ascii=False)
                
                if options:
                    for opt in options:
                        opt = opt.strip()
                        if not opt: continue
                        es_correcta = opt.startswith(correcta)
                        fb = combined_feedback if es_correcta else None
                        cur.execute(
                            "INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta, feedback) VALUES (%s, %s, %s, %s)",
                            (preg_id, opt, es_correcta, fb)
                        )
                else:
                    cur.execute(
                        "INSERT INTO CUESTIONARIOS_RESPUESTAS (pregunta_id, texto_opcion, es_correcta, feedback) VALUES (%s, %s, TRUE, %s)",
                        (preg_id, correcta, combined_feedback)
                    )
                
    conn.commit()
    cur.close()
    conn.close()
    print("Migración completada con éxito.")

if __name__ == "__main__":
    migrate()
