import psycopg2
import os

conn = psycopg2.connect(
    host="localhost",
    database="RasaDB",
    user="postgre",
    password="RasaChatBot_2026",
    port=5432
)
cur = conn.cursor()
sender_id = '6266468745'
cur.execute("SELECT nombre FROM ALUMNOS WHERE rasa_sender_id = %s", (sender_id,))
print("Result:", cur.fetchone())
conn.close()
