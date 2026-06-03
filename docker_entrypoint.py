"""
Script de inicialización (Entrypoint) para el contenedor de Rasa en Docker.

Este script se encarga de:
1. Esperar a que el servicio de Ngrok esté disponible y obtener su URL pública.
2. Inyectar dinámicamente la URL de Ngrok y los tokens de Telegram en 'credentials.yml'.
3. Configurar el webhook en la API de Telegram.
4. Entrenar el modelo de Rasa si no existe uno previo.
5. Iniciar el servidor de Rasa.
"""

import urllib.request
import urllib.parse
import json
import time
import os
import subprocess
import sys

def main():
    """
    Función principal que orquesta la configuración e inicialización del servidor Rasa.
    """
    print("Iniciando docker_entrypoint.py...")
    
    ngrok_url = None
    urls_to_try = ["http://ngrok:4040/api/tunnels", "http://localhost:4040/api/tunnels", "http://127.0.0.1:4040/api/tunnels"]
    print("Esperando a que Ngrok inicie...")
    for i in range(15):
        print("Intento", i+1)
        for url in urls_to_try:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=2) as response:
                    data = json.loads(response.read().decode())
                    if len(data.get('tunnels', [])) > 0:
                        ngrok_url = data['tunnels'][0]['public_url']
                        # Buscar la URL segura (HTTPS) en la respuesta
                        for tunnel in data['tunnels']:
                            if tunnel['public_url'].startswith("https"):
                                ngrok_url = tunnel['public_url']
                                break
                        break
            except Exception as e:
                pass
        
        if ngrok_url:
            break
            
        time.sleep(2)
        
    if not ngrok_url:
        print("ERROR: No se pudo obtener la URL de Ngrok. Verifica que el servicio ngrok funciona.")
        sys.exit(1)
        
    print(f"Ngrok URL obtenida: {ngrok_url}")
    
    # Actualizar credentials.yml manualmente mediante reemplazo de cadenas
    credentials_path = "/app/credentials.yml"
    if os.path.exists(credentials_path):
        with open(credentials_path, "r") as f:
            lines = f.readlines()
            
        telegram_token = os.environ.get("TELEGRAM_TOKEN", "")
        telegram_verify = os.environ.get("TELEGRAM_VERIFY_NAME", "")
        
        in_telegram = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            
            # Comprobación básica para identificar la sección de Telegram
            if stripped == "telegram:":
                in_telegram = True
            elif in_telegram and stripped and not line.startswith(" ") and not line.startswith("\t") and not stripped.startswith("#"):
                # Si encontramos una nueva clave de nivel raíz sin comentar, hemos salido de la sección de Telegram
                in_telegram = False
                
            if in_telegram and stripped.startswith("webhook_url:"):
                # Reemplazar webhook_url
                new_line = line[:len(line) - len(line.lstrip())] # Preservar la indentación original
                new_lines.append(f'{new_line}webhook_url: "{ngrok_url}/webhooks/telegram/webhook"\n')
            elif in_telegram and stripped.startswith("access_token:") and telegram_token:
                new_line = line[:len(line) - len(line.lstrip())]
                new_lines.append(f'{new_line}access_token: "{telegram_token}"\n')
            elif in_telegram and stripped.startswith("verify:") and telegram_verify:
                new_line = line[:len(line) - len(line.lstrip())]
                new_lines.append(f'{new_line}verify: "{telegram_verify}"\n')
            else:
                new_lines.append(line)
                
        with open(credentials_path, "w") as f:
            f.writelines(new_lines)
        print("credentials.yml actualizado con la nueva URL de Ngrok y tokens de entorno.")
    else:
        print("WARNING: No se encontró credentials.yml en /app. Se usará configuración por defecto.")
        
    # Registrar Webhook en la API de Telegram
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if telegram_token:
        print("Enviando webhook a Telegram...")
        telegram_api_url = f"https://api.telegram.org/bot{telegram_token}/setWebhook"
        webhook_data = urllib.parse.urlencode({
            "url": f"{ngrok_url}/webhooks/telegram/webhook"
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(telegram_api_url, data=webhook_data)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                if result.get("ok"):
                    print("Webhook de Telegram configurado exitosamente.")
                else:
                    print(f"ERROR en Telegram: {result}")
        except Exception as e:
            print(f"ERROR configurando Telegram: {e}")
            
    # Entrenar el Modelo
    print("Entrenando el modelo de Rasa (si es necesario)...")
    subprocess.run(["rasa", "train"], check=False)
    
    # Iniciar el Servidor Rasa
    print("Iniciando servidor de Rasa...")
    cmd = ["rasa", "run", "--enable-api", "--cors", "*", "--debug", 
           "--credentials", "credentials.yml", 
           "--endpoints", "endpoints.yml", 
           "--port", "5005"]
    
    # Reemplazar el proceso actual con el proceso de Rasa
    os.execvp("rasa", cmd)

if __name__ == "__main__":
    main()
