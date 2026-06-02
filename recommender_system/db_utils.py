import os
import psycopg2

# Cargar variables de entorno desde el archivo .env si existe
# (Ejecutado dentro del contenedor de Docker, el entorno ya está cargado)

def get_db_connection():
    """Crea y devuelve una conexión a la base de datos PostgreSQL usando variables de entorno."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres_db"),
        database=os.environ.get("DB_NAME", "RasaDB"),
        user=os.environ.get("DB_USER", "postgre"),
        password=os.environ.get("DB_PASSWORD", "RasaChatBot_2026"),
        port=int(os.environ.get("DB_PORT", 5432))
    )

def get_num_temas(asignatura_id=1):
    """Obtiene el número de temas de la base de datos para la asignatura dada."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM TEMAS WHERE asignatura_id = %s", (asignatura_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Error al conectar a la base de datos o consultar temas: {e}")
        print("Asegúrate de que la base de datos esté corriendo y el archivo .env configurado correctamente.")
        # Valor de fallback por seguridad
        return 6
