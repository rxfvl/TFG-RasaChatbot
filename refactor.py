import re

def refactor_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 1. load_preguntas
    content = content.replace('''        conn = get_db_connection()
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
        rows = cur.fetchall()''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
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
                rows = cur.fetchall()''')
    
    content = content.replace('''        cur.close()
        conn.close()
    except Exception as e:
        print(f"[load_preguntas] Error: {e}")''', '''    except Exception as e:
        print(f"[load_preguntas] Error: {e}")''')

    # 2. load_conceptos
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            SELECT ct.id, ct.termino, ct.termino_legible, ct.definicion
            FROM CONCEPTOS_TEORICOS ct
            JOIN TEMAS t ON ct.tema_id = t.id
            WHERE t.numero = %s AND t.asignatura_id = %s
            ORDER BY ct.id ASC
        """
        cur.execute(query, (tema_num, ASIGNATURA_ID_ACTIVA))
        rows = cur.fetchall()''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT ct.id, ct.termino, ct.termino_legible, ct.definicion
                    FROM CONCEPTOS_TEORICOS ct
                    JOIN TEMAS t ON ct.tema_id = t.id
                    WHERE t.numero = %s AND t.asignatura_id = %s
                    ORDER BY ct.id ASC
                """
                cur.execute(query, (tema_num, ASIGNATURA_ID_ACTIVA))
                rows = cur.fetchall()''')
    
    content = content.replace('''        cur.close()
        conn.close()
    except Exception as e:
        print(f"[load_conceptos] Error: {e}")''', '''    except Exception as e:
        print(f"[load_conceptos] Error: {e}")''')

    # 3. load_todos_los_temas
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT numero FROM TEMAS WHERE asignatura_id = %s ORDER BY numero ASC",
            (ASIGNATURA_ID_ACTIVA,)
        )
        temas = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT numero FROM TEMAS WHERE asignatura_id = %s ORDER BY numero ASC",
                    (ASIGNATURA_ID_ACTIVA,)
                )
                temas = [row[0] for row in cur.fetchall()]''')

    # 4. guardar_interaccion
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
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
        conn.commit()
        cur.close()
        conn.close()''', '''        with get_db_connection() as conn:
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
                )''')

    # 5. esta_matriculado
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM MATRICULAS
            WHERE alumno_id = %s AND asignatura_id = %s
            """,
            (alumno_id, asignatura_id)
        )
        result = cur.fetchone() is not None
        cur.close()
        conn.close()
        return result''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM MATRICULAS
                    WHERE alumno_id = %s AND asignatura_id = %s
                    """,
                    (alumno_id, asignatura_id)
                )
                return cur.fetchone() is not None''')

    # 6. iniciar_seguimiento
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO SEGUIMIENTO (alumno_id, cuestionario_id)
            VALUES (%s, %s)
            RETURNING id
            """,
            (alumno_id, cuestionario_id)
        )
        seguimiento_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return seguimiento_id''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO SEGUIMIENTO (alumno_id, cuestionario_id)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (alumno_id, cuestionario_id)
                )
                return cur.fetchone()[0]''')

    # 7. guardar_detalle_respuesta
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO SEGUIMIENTO_DETALLE (seguimiento_id, pregunta_id, respuesta_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (seguimiento_id, pregunta_id) DO UPDATE
                SET respuesta_id = EXCLUDED.respuesta_id
            """,
            (seguimiento_id, pregunta_id, respuesta_id)
        )
        conn.commit()
        cur.close()
        conn.close()''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO SEGUIMIENTO_DETALLE (seguimiento_id, pregunta_id, respuesta_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (seguimiento_id, pregunta_id) DO UPDATE
                        SET respuesta_id = EXCLUDED.respuesta_id
                    """,
                    (seguimiento_id, pregunta_id, respuesta_id)
                )''')

    # 8. actualizar_puntuacion
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE SEGUIMIENTO SET puntuacion_total = %s WHERE id = %s",
            (puntuacion, seguimiento_id)
        )
        conn.commit()
        cur.close()
        conn.close()''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE SEGUIMIENTO SET puntuacion_total = %s WHERE id = %s",
                    (puntuacion, seguimiento_id)
                )''')

    # 9. get_cuestionario_id
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()
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
        cur.close()
        conn.close()
        return row[0] if row else None''', '''        with get_db_connection() as conn:
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
                return row[0] if row else None''')

    # 10. get_progreso_alumno
    content = content.replace('''        conn = get_db_connection()
        cur = conn.cursor()

        # ── 1. Actividad general desde INTERACCIONES_CHAT ──────────────────''', '''        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # ── 1. Actividad general desde INTERACCIONES_CHAT ──────────────────''')
                
    content = content.replace('''        cur.close()
        conn.close()
    except Exception as e:
        print(f"[get_progreso_alumno] Error: {e}")''', '''    except Exception as e:
        print(f"[get_progreso_alumno] Error: {e}")''')

    # Fix indentation in get_progreso_alumno body manually
    # Just fix the few cur.execute calls inside get_progreso_alumno to match the new indentation
    lines = content.split('\n')
    in_progreso = False
    new_lines = []
    for line in lines:
        if 'def get_progreso_alumno' in line:
            in_progreso = True
        if in_progreso and 'except Exception as e:' in line:
            in_progreso = False
            
        if in_progreso and 'with get_db_connection() as conn:' in line:
            new_lines.append(line)
            continue
        if in_progreso and 'with conn.cursor() as cur:' in line:
            new_lines.append(line)
            continue
            
        # The body inside the with was 8 spaces, it needs to be 16 for cur.execute, wait.
        # It's easier to just do it simply:
        if in_progreso and line.startswith('        ') and not line.startswith('            '):
            if not line.startswith('        with'):
                new_lines.append('    ' + line)
                continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)


    # 11. ActionCheckRegistro
    content = content.replace('''            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM ALUMNOS WHERE rasa_sender_id = %s", (sender_id,))
            alumno = cur.fetchone()
            cur.close()
            conn.close()
            if alumno:''', '''            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nombre FROM ALUMNOS WHERE rasa_sender_id = %s", (sender_id,))
                    alumno = cur.fetchone()
                    if alumno:''')

    # 12. ActionGuardarAlumno
    content = content.replace('''            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO ALUMNOS (rasa_sender_id, nombre, correo) VALUES (%s, %s, %s) ON CONFLICT (rasa_sender_id) DO NOTHING",
                (sender_id, nombre, correo)
            )
            conn.commit()
            cur.close()
            conn.close()''', '''            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO ALUMNOS (rasa_sender_id, nombre, correo) VALUES (%s, %s, %s) ON CONFLICT (rasa_sender_id) DO NOTHING",
                        (sender_id, nombre, correo)
                    )''')

    # 13. ActionDarConcepto
    content = content.replace('''            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT termino_legible, definicion FROM CONCEPTOS_TEORICOS WHERE id = %s",
                (concepto_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:''', '''            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT termino_legible, definicion FROM CONCEPTOS_TEORICOS WHERE id = %s",
                        (concepto_id,)
                    )
                    row = cur.fetchone()

            if row:''')

    with open(filepath, 'w') as f:
        f.write(content)

refactor_file("actions/actions.py")
