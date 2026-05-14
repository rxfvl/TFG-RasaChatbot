import urllib.request
import urllib.parse
import json
import time
import os
import subprocess
import sys

def main():
    print("🟡 Iniciando docker_entrypoint.py...")
    
    # 1. Wait for ngrok to be up and fetch URL
    ngrok_url = None
    print("🟡 Esperando a que Ngrok inicie...")
    for i in range(15):
        try:
            req = urllib.request.Request("http://ngrok:4040/api/tunnels")
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode())
                if len(data.get('tunnels', [])) > 0:
                    ngrok_url = data['tunnels'][0]['public_url']
                    # Some ngrok versions return both http and https, find https
                    for tunnel in data['tunnels']:
                        if tunnel['public_url'].startswith("https"):
                            ngrok_url = tunnel['public_url']
                            break
                    break
        except Exception as e:
            pass
        time.sleep(2)
        
    if not ngrok_url:
        print("🔴 ERROR: No se pudo obtener la URL de Ngrok. Verifica que el servicio ngrok funciona.")
        sys.exit(1)
        
    print(f"🟢 Ngrok URL obtenida: {ngrok_url}")
    
    # 2. Update credentials.yml manually via string replacement to preserve formatting/comments
    # We use simple string replacement instead of yaml module to avoid needing PyYAML if not available 
    # (though PyYAML is available in Rasa, it sometimes strips comments).
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
            
            # Simple check for telegram section
            if stripped == "telegram:":
                in_telegram = True
            elif in_telegram and stripped and not line.startswith(" ") and not line.startswith("\t") and not stripped.startswith("#"):
                # If we encounter a new root-level key that is not commented, we are out of telegram
                in_telegram = False
                
            if in_telegram and stripped.startswith("webhook_url:"):
                # Replace webhook_url
                new_line = line[:len(line) - len(line.lstrip())] # Preserve indentation
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
        print("🟢 credentials.yml actualizado con la nueva URL de Ngrok y tokens de entorno.")
    else:
        print("🟡 WARNING: No se encontró credentials.yml en /app. Se usará configuración por defecto.")
        
    # 3. Register Webhook in Telegram API
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if telegram_token:
        print("🔁 Enviando webhook a Telegram...")
        telegram_api_url = f"https://api.telegram.org/bot{telegram_token}/setWebhook"
        webhook_data = urllib.parse.urlencode({
            "url": f"{ngrok_url}/webhooks/telegram/webhook"
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(telegram_api_url, data=webhook_data)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                if result.get("ok"):
                    print("🟢 Webhook de Telegram configurado exitosamente.")
                else:
                    print(f"🔴 ERROR en Telegram: {result}")
        except Exception as e:
            print(f"🔴 ERROR configurando Telegram: {e}")
            
    # 4. Train Model
    print("🧠 Entrenando el modelo de Rasa (si es necesario)...")
    subprocess.run(["rasa", "train"], check=False)
    
    # 5. Start Rasa Server
    print("🚀 Iniciando servidor de Rasa...")
    cmd = ["rasa", "run", "--enable-api", "--cors", "*", "--debug", 
           "--credentials", "credentials.yml", 
           "--endpoints", "endpoints.yml", 
           "--port", "5005"]
    
    # Replace the current process with Rasa
    os.execvp("rasa", cmd)

if __name__ == "__main__":
    main()
