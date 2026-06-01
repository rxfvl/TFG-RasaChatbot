import os
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"), # using localhost for local run
        database=os.environ.get("POSTGRES_DB", "RasaDB"),
        user=os.environ.get("POSTGRES_USER", "postgre"),
        password=os.environ.get("POSTGRES_PASSWORD", "RasaChatBot_2026"),
        port=int(os.environ.get("DB_PORT", 5432))
    )

def apply_migration():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Alter table
        print("Modificando tabla CLASE_HORARIO...")
        try:
            cur.execute("ALTER TABLE CLASE_HORARIO ADD COLUMN aula VARCHAR(150);")
        except psycopg2.errors.DuplicateColumn:
            print("  La columna 'aula' ya existe.")
            conn.rollback()
        else:
            conn.commit()

        # 2. Insertar Tutorias
        print("Insertando tutorías...")
        cur.execute("""
            INSERT INTO TUTORIAS (profesor_id, dia_semana, hora_inicio, hora_fin) VALUES 
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), 'lunes', '09:00', '11:00'),
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), 'martes', '08:00', '10:00')
            ON CONFLICT DO NOTHING;
        """)
        
        # 3. Insertar Clases
        print("Insertando clases...")
        cur.execute("""
            INSERT INTO CLASE_HORARIO (profesor_id, asignatura_id, grupo, dia_semana, hora_inicio, hora_fin, aula) VALUES 
            -- Teoría
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 'GG1', 'martes', '12:00', '13:30', 'aula B9 del Aulario Averroes en Campus de Rabanales'),
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 'GG1', 'jueves', '09:00', '10:30', 'aula B9 del Aulario Averroes en Campus de Rabanales'),
            -- Práctica
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 'GM1', 'lunes', '11:00', '13:00', 'aula p1 del Ramón y Cajal'),
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 'GM1', 'miercoles', '09:00', '11:00', 'aula s1 del Ramón y Cajal'),
            ((SELECT id FROM PROFESORES WHERE correo = 'in1zagoa@uco.es'), (SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'), 'GM1', 'viernes', '13:00', '15:00', 'aula p1 del Ramón y Cajal');
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("Migración de horarios aplicada con éxito.")
    except Exception as e:
        print(f"Error en la migración: {e}")

if __name__ == "__main__":
    apply_migration()
