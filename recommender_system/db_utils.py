"""
Módulo de utilidades para la conexión y consulta a la base de datos PostgreSQL.

Proporciona funciones para establecer la conexión con la base de datos utilizando
variables de entorno y para realizar consultas básicas necesarias para el
sistema de recomendación.
"""

import os
import psycopg2


def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos PostgreSQL utilizando
    las credenciales configuradas en las variables de entorno.
    
    Returns:
        psycopg2.extensions.connection: Objeto de conexión a la base de datos.
    """
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres_db"),
        database=os.environ.get("DB_NAME", "RasaDB"),
        user=os.environ.get("DB_USER", "postgre"),
        password=os.environ.get("DB_PASSWORD", "RasaChatBot_2026"),
        port=int(os.environ.get("DB_PORT", 5432))
    )

def get_num_temas(asignatura_id=1):
    """
    Consulta la base de datos para obtener el número total de temas asociados a una asignatura.
    
    Args:
        asignatura_id (int, opcional): Identificador de la asignatura. Por defecto es 1.
        
    Returns:
        int: Número de temas encontrados. En caso de error de conexión, devuelve un valor de seguridad (6).
    """
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
