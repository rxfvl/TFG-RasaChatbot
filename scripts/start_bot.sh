#!/bin/bash

# 🔧 CONFIGURA TU TOKEN AQUÍ
TELEGRAM_TOKEN="5388935623:AAEYjIPaXy732pZVlWFjwdk_I2jwRiiMiOM"
VERIFY_NAME="UcoLogibot"

# 🔄 Lanzar ngrok en segundo plano
echo "🟡 Iniciando ngrok..."
pkill ngrok > /dev/null 2>&1
ngrok http 5005 > /dev/null &
sleep 3  # Esperar a que ngrok se inicie

# 🔍 Obtener la URL pública
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
echo "🟢 Ngrok URL: $NGROK_URL"

# ✍️ Actualizar credentials.yml (opcional, si quieres que el archivo siempre esté sincronizado)
sed -i.bak "s|webhook_url:.*|webhook_url: \"$NGROK_URL/webhooks/telegram/webhook\"|" credentials.yml

# 📡 Enviar webhook a Telegram
echo "🔁 Enviando webhook a Telegram..."
curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook" \
     -d "url=$NGROK_URL/webhooks/telegram/webhook" | jq

# 🧠 Entrenar modelo (opcional, solo si quieres asegurar que esté actualizado)
rasa train --force

# 🚀 Iniciar Rasa
echo "🚀 Iniciando servidor de Rasa..."
rasa run --enable-api --cors "*" --debug --credentials credentials.yml --endpoints endpoints.yml --port 5005
