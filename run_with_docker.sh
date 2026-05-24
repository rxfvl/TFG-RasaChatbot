#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

echo "🐳 Iniciando configuración sin docker-compose (Solo Docker)..."

# 1. Cargar variables de entorno del archivo .env si existe
if [ -f .env ]; then
    echo "🟢 Cargando variables desde .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo "🔴 ERROR: No se encontró el archivo .env en el directorio actual."
    echo "Por favor, crea un archivo .env basado en tu configuración."
    exit 1
fi

# Validar que NGROK_AUTHTOKEN esté configurado
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "⚠️ ADVERTENCIA: NGROK_AUTHTOKEN no está definido en tu archivo .env."
    echo "Ngrok podría no funcionar correctamente sin un token."
fi

# 2. Crear la red de Docker si no existe
echo "🌐 Creando red de Docker 'rasa-network'..."
docker network create rasa-network 2>/dev/null || true

# 3. Limpiar contenedores antiguos con el mismo nombre si existen
echo "🧹 Limpiando contenedores antiguos..."
docker rm -f postgres_db rasa_action_server ngrok rasa_server 2>/dev/null || true

# 4. Levantar la Base de Datos PostgreSQL
echo "💾 Levantando contenedor de Base de Datos (postgres_db)..."
docker run -d \
  --name postgres_db \
  --network rasa-network \
  -p 5432:5432 \
  -e POSTGRES_USER="$DB_USER" \
  -e POSTGRES_PASSWORD="$DB_PASSWORD" \
  -e POSTGRES_DB="$DB_NAME" \
  -v postgres_data:/var/lib/postgresql/data \
  -v "$(pwd)/script_bbdd.sql:/docker-entrypoint-initdb.d/init.sql" \
  postgres:15

# 5. Levantar el Servidor de Acciones (Rasa SDK)
echo "⚡ Levantando contenedor de Servidor de Acciones (rasa_action_server)..."
docker run -d \
  --name rasa_action_server \
  --network rasa-network \
  -p 5055:5055 \
  -e POSTGRES_USER="$DB_USER" \
  -e POSTGRES_PASSWORD="$DB_PASSWORD" \
  -e POSTGRES_DB="$DB_NAME" \
  -v "$(pwd)/actions:/app/actions" \
  -v "$(pwd)/requirements.txt:/app/requirements.txt" \
  --user root \
  rasa/rasa-sdk:latest \
  run sh -c "pip install --no-cache-dir psycopg2-binary && python -m rasa_sdk --actions actions"

# 6. Levantar Ngrok
echo "🔗 Levantando contenedor de Ngrok (ngrok)..."
docker run -d \
  --name ngrok \
  --network rasa-network \
  -v "$(pwd)/ngrok.yml:/etc/ngrok.yml" \
  -e NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN" \
  ngrok/ngrok:latest \
  http rasa_server:5005 --config /etc/ngrok.yml

# 7. Levantar el Servidor Rasa (Core y NLU)
echo "🚀 Levantando contenedor de Rasa Server (rasa_server)..."
echo "Nota: Esto entrenará el modelo e iniciará el bot..."
docker run -d \
  --name rasa_server \
  --network rasa-network \
  -p 5005:5005 \
  -v "$(pwd):/app" \
  -e TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
  -e TELEGRAM_VERIFY_NAME="$TELEGRAM_VERIFY_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e DB_NAME="$DB_NAME" \
  --user root \
  --entrypoint "" \
  rasa/rasa:latest-full \
  sh -c "python /app/docker_entrypoint.py"
