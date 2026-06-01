#!/bin/bash

echo "Selecciona qué logs quieres ver en tiempo real:"
echo "1) Servidor de Acciones (actions.py) - 🔴 ¡Aquí ocurren el 90% de los errores de código!"
echo "2) Servidor de Rasa (NLU y Core)"
echo "3) Base de datos PostgreSQL"
echo "4) Todos los contenedores a la vez"
echo "5) Salir"

read -p "Opción (1-5): " opcion

case $opcion in
  1)
    echo "👀 Mostrando logs de rasa_action_server (Pulsa Ctrl+C para salir)..."
    docker logs -f --tail 50 rasa_action_server
    ;;
  2)
    echo "👀 Mostrando logs de rasa_server (Pulsa Ctrl+C para salir)..."
    docker logs -f --tail 50 rasa_server
    ;;
  3)
    echo "👀 Mostrando logs de postgres_db (Pulsa Ctrl+C para salir)..."
    docker logs -f --tail 50 postgres_db
    ;;
  4)
    echo "👀 Mostrando logs de todos los contenedores (Pulsa Ctrl+C para salir)..."
    docker logs -f --tail 50
    ;;
  5)
    echo "Saliendo..."
    exit 0
    ;;
  *)
    echo "Opción no válida."
    ;;
esac
