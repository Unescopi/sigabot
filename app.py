from flask import Flask, request, jsonify
import os
import logging
import requests
from waitress import serve
from dotenv import load_dotenv
from services.database import Database
import sys

# Configuração básica
load_dotenv()
app = Flask(__name__)
db = Database()

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def send_message(group_id, text):
    try:
        url = f"{os.getenv('SERVER_URL')}/message/sendText/{os.getenv('INSTANCE')}"
        payload = {"number": group_id, "text": text}
        headers = {"apikey": os.getenv('APIKEY')}
        response = requests.post(url, json=payload, headers=headers)
        return response.ok
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        logger.info("Webhook recebido")
        
        if not data:
            return jsonify({"status": True}), 200
            
        if data.get('event') == 'messages.upsert':
            message = data.get('data', {})
            group_id = message.get('key', {}).get('remoteJid')
            text = message.get('message', {}).get('conversation')
            
            logger.info(f"Mensagem recebida: {text}")
            
            if text and group_id in [os.getenv('GROUP_ID'), os.getenv('GROUP_TEST_ID')]:
                if "fechado" in text.lower():
                    lado = "Goioerê" if "goioerê" in text.lower() else "Quarto Centenário"
                    db.atualizar_status(lado, "FECHADO")
                    outro = "Goioerê" if lado == "Quarto Centenário" else "Quarto Centenário"
                    db.atualizar_status(outro, "LIBERADO")
                    
                    msg = f"⚠️ ATENÇÃO ⚠️\n\n🔴 {lado}: FECHADO\n🟢 {outro}: LIBERADO"
                    send_message(group_id, msg)
                    logger.info("Mensagem enviada")
        
        return jsonify({"status": True}), 200
    except Exception as e:
        logger.error(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("=== INICIANDO SERVIDOR ===")
    serve(app, host='0.0.0.0', port=int(os.getenv('PORT', 80))) 