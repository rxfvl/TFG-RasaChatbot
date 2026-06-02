"""
Script de migración de conceptos teóricos.
Extrae las definiciones del Material-Temario.pdf e inserta todos los temas
y sus conceptos en la base de datos. Los conceptos antiguos se eliminan y
se reemplazan con los del PDF para garantizar consistencia.
"""
import os
import psycopg2

# ---------------------------------------------------------------------------
# Conexión a la base de datos
# ---------------------------------------------------------------------------

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres_db"),
        database=os.environ.get("POSTGRES_DB", "RasaDB"),
        user=os.environ.get("POSTGRES_USER", "postgre"),
        password=os.environ.get("POSTGRES_PASSWORD", "RasaChatBot_2026"),
        port=int(os.environ.get("DB_PORT", 5432))
    )

# ---------------------------------------------------------------------------
# Datos extraídos del PDF Material-Temario.pdf
# Cada entrada: (tema_numero, termino_slug, termino_legible, definicion)
# ---------------------------------------------------------------------------

CONCEPTOS_POR_TEMA = {
    1: {
        "titulo": "Tema 1",
        "conceptos": [
            (
                "sistema_comunicacion",
                "Sistema de comunicación",
                "Un sistema de comunicación es un conjunto de elementos y dispositivos involucrados en el intercambio eficaz de información entre dos puntos remotos."
            ),
            (
                "red_computadoras",
                "Red de computadoras",
                "La red de computadoras es un conjunto de equipos terminales autónomos e interconectados."
            ),
            (
                "servicio_capa",
                "Servicio de capa",
                "El servicio que ofrece una capa indica qué hace la capa, qué servicios brinda a la capa superior. Define el aspecto semántico (significado) de la capa, no la forma en que la capa superior tiene acceso al servicio."
            ),
            (
                "protocolo",
                "Protocolo",
                "El protocolo es un conjunto de normas, o un acuerdo, que determina el formato y la transmisión de datos entre capas homólogas en equipos distintos. Son las reglas de comunicación entre capas idénticas."
            ),
            (
                "modelo_referencia",
                "Modelo de referencia",
                "El modelo de referencia es el conjunto de capas definido y las funciones asociadas al mismo."
            ),
        ]
    },
    2: {
        "titulo": "Tema 2",
        "conceptos": [
            (
                "conmutacion",
                "Conmutación",
                "La Conmutación consiste en establecer un camino entre dos puntos, un emisor y un receptor a través de nodos y líneas de transmisión. La conmutación permite la entrega de la señal desde el origen hasta el destino requerido. Existen diferentes técnicas de conmutación según como se establezca dicho camino: circuitos y paquetes."
            ),
            (
                "enrutamiento",
                "Algoritmo de enrutamiento",
                "El algoritmo de enrutamiento es la parte de software de la capa de red encargada de decidir la línea de salida por la que se retransmite un paquete de entrada."
            ),
            (
                "capa_red",
                "Capa de Red",
                "La Capa de Red tiene entre sus funciones el encaminamiento, el control de congestión y la interconexión entre redes."
            ),
            (
                "congestion",
                "Congestión",
                "La congestión se produce cuando la carga (temporalmente) es superior (en una parte del sistema) a la que pueden manejar los recursos."
            ),
            (
                "calidad_servicio",
                "Calidad de servicio",
                "La calidad de servicio hace referencia a los procedimientos utilizados para gestionar el tráfico de una red y garantizar un cierto nivel de rendimiento según el tipo de aplicación."
            ),
        ]
    },
    3: {
        "titulo": "Tema 3",
        "conceptos": [
            (
                "ip_caracteristicas",
                "Protocolo IP",
                "Las principales características del protocolo IP son: es sin conexión, del mejor esfuerzo e independiente de los medios."
            ),
            (
                "nat",
                "NAT (Network Address Translation)",
                "La traducción de direcciones de red (NAT, Network Address Translation) es un mecanismo que permite traducir una dirección IP privada a una dirección IP pública de forma que los paquetes pertenecientes a un host puedan ser enrutados."
            ),
            (
                "icmp",
                "ICMP",
                "ICMP es un protocolo de mensajes de control en Internet, que entre otros eventos puede informar de: destino inalcanzable, tiempo excedido, mensajes de eco y respuesta."
            ),
            (
                "dhcp",
                "DHCP",
                "DHCP es un protocolo que permite asignar direcciones IP tanto de forma automática, como manual, como dinámica."
            ),
            (
                "sistema_autonomo",
                "Sistema autónomo",
                "Un sistema autónomo es un conjunto de subredes, y el hardware asociado, administradas por una única autoridad, de forma que en ella se puede implementar un algoritmo de encaminamiento independiente de los considerados en otros sistemas autónomos."
            ),
        ]
    },
    4: {
        "titulo": "Tema 4",
        "conceptos": [
            (
                "repetidor",
                "Repetidor",
                "Los repetidores (repeater) trabajan en el nivel físico, interconectando dos segmentos de LAN. Un repetidor, en cada dirección, regenera las señales eléctricas recibidas de un segmento y las reenvía al otro segmento."
            ),
            (
                "hub",
                "Hub",
                "Un hub es un multirepetidor operando a nivel de bit. Repiten los bits recibidos en una interfaz por todas las otras interfaces."
            ),
            (
                "router",
                "Router",
                "Un router (enrutador o encaminador) se trata de un dispositivo hardware o software para interconexión de redes de computadoras que opera en la capa tres (nivel de red) del modelo OSI. El router interconecta segmentos de red o redes enteras. Hace pasar paquetes de datos entre redes tomando como base la información de la capa de red."
            ),
            (
                "tunelizacion",
                "Tunelización",
                "La tunelización permite la interconexión entre host de origen y de destino que están en el mismo tipo de red, pero hay una red diferente en medio."
            ),
            (
                "fragmentacion",
                "Fragmentación de paquetes",
                "La fragmentación de paquetes puede ser transparente. La Fragmentación transparente resulta transparente para cualquier red subsecuente por la que deba pasar el paquete en su camino hacia el destino final debido a que se reensambla el paquete. En la fragmentación no transparente, una vez que se ha fragmentado un paquete, cada fragmento se trata como si fuera un paquete original. La recombinación ocurre sólo en el host de destino."
            ),
        ]
    },
    5: {
        "titulo": "Tema 5",
        "conceptos": [
            (
                "capa_transporte",
                "Capa de transporte",
                "La capa de transporte se encarga de proporcionar un transporte de datos confiable, eficiente y económico de la máquina de origen a destino, independientemente de la red o redes físicas en uso."
            ),
            (
                "udp",
                "Protocolo UDP",
                "El protocolo UDP proporciona una forma para que las aplicaciones envíen datagramas IP encapsulados sin tener que establecer una conexión utilizando la política del mejor esfuerzo."
            ),
            (
                "tcp",
                "Protocolo TCP",
                "El protocolo TCP proporciona un flujo de bytes confiable de extremo a extremo a través de una interred no confiable."
            ),
            (
                "iana",
                "IANA",
                "La Autoridad de Números Asignados de Internet (IANA) es el organismo de estandarización que se encarga de asignar diversos estándares de direccionamiento, incluidos los números de puerto."
            ),
            (
                "desempeno_transporte",
                "Desempeño en la capa de transporte",
                "Se pueden considerar cuatro aspectos de desempeño a nivel de capa de transporte: los problemas del diseño en el desempeño, medición del desempeño, diseño de sistemas con mejor desempeño y procesamiento rápido de las unidades de datos del protocolo de transporte."
            ),
        ]
    },
    6: {
        "titulo": "Tema 6",
        "conceptos": [
            (
                "capa_aplicacion",
                "Capa de aplicación",
                "La capa de aplicación se encarga de definir los protocolos de aplicaciones que el usuario requiere con frecuencia."
            ),
            (
                "dns",
                "Protocolo DNS",
                "El protocolo DNS (Servidor de Nombres de Dominio) es un sistema de nomenclatura jerárquico descentralizado para dispositivos conectados a redes IP como Internet o una red privada. Este sistema asocia diferente información con los nombres de dominio asignados."
            ),
            (
                "http",
                "Protocolo HTTP",
                "El protocolo HTTP (Protocolo de Transferencia de Hipertexto) es un protocolo de comunicación que se emplea para transferir información a través de la World Wide Web."
            ),
            (
                "smtp",
                "Protocolo SMTP",
                "El protocolo SMTP (Protocolo para la Transferencia Simple de Correo) es un protocolo de red que se emplea para enviar y recibir correos electrónicos (emails)."
            ),
            (
                "streaming",
                "Streaming multimedia",
                "Streaming multimedia significa que los datos se envían hacia el ordenador del cliente y se reproducen al mismo tiempo."
            ),
        ]
    },
}


# ---------------------------------------------------------------------------
# Lógica de migración
# ---------------------------------------------------------------------------

def migrate():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Asegurar que la asignatura 'Redes' existe
    cur.execute("SELECT id FROM ASIGNATURAS WHERE nombre = 'Redes'")
    asig_row = cur.fetchone()
    if not asig_row:
        cur.execute(
            "INSERT INTO ASIGNATURAS (nombre, titulacion, curso, enlace_guia_docente) "
            "VALUES ('Redes', 'Ingeniería Informática', 'tercero', '') RETURNING id"
        )
        asig_id = cur.fetchone()[0]
        print("🟢 Asignatura 'Redes' creada.")
    else:
        asig_id = asig_row[0]
        print(f"ℹ️  Asignatura 'Redes' ya existe (id={asig_id}).")

    for tema_num, tema_data in CONCEPTOS_POR_TEMA.items():
        titulo = tema_data["titulo"]
        conceptos = tema_data["conceptos"]

        # 2. Asegurar que el tema existe
        cur.execute(
            "SELECT id FROM TEMAS WHERE asignatura_id = %s AND numero = %s",
            (asig_id, tema_num)
        )
        tema_row = cur.fetchone()
        if not tema_row:
            cur.execute(
                "INSERT INTO TEMAS (asignatura_id, numero, titulo) VALUES (%s, %s, %s) RETURNING id",
                (asig_id, tema_num, titulo)
            )
            tema_id = cur.fetchone()[0]
            print(f"🟢 Tema {tema_num} creado (id={tema_id}).")
        else:
            tema_id = tema_row[0]
            print(f"ℹ️  Tema {tema_num} ya existe (id={tema_id}).")

        # 3. Eliminar los conceptos antiguos de este tema para reemplazarlos
        for termino, termino_legible, definicion in conceptos:
            cur.execute("SELECT id FROM CONCEPTOS_TEORICOS WHERE tema_id = %s AND termino = %s", (tema_id, termino))
            if cur.fetchone():
                print(f"⚠️ El concepto '{termino_legible}' ya existe en la base de datos. Saltando...")
                continue
            
            cur.execute(
                "INSERT INTO CONCEPTOS_TEORICOS (tema_id, termino, termino_legible, definicion) VALUES (%s, %s, %s, %s)",
                (tema_id, termino, termino_legible, definicion)
            )
            print(f"   ✅ Concepto '{termino_legible}' insertado en Tema {tema_num}.")

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 Migración completada con éxito. Datos de alumnos y cuestionarios conservados.")


if __name__ == "__main__":
    migrate()
