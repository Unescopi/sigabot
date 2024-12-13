from flask import Flask, request, jsonify
import os
import logging
from services.evolution_service import process_message
import requests
from waitress import serve
from dotenv import load_dotenv
from services.database import Database

# Configuração básica
load_dotenv()
app = Flask(__name__)
db = Database()

# Rota webhook simplificada
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": True}), 200
            
        if data.get('event') == 'messages.upsert':
            message = data.get('data', {})
            group_id = message.get('key', {}).get('remoteJid')
            text = message.get('message', {}).get('conversation')
            
            if text and group_id in [os.getenv('GROUP_ID'), os.getenv('GROUP_TEST_ID')]:
                if "fechado" in text.lower():
                    lado = "Goioerê" if "goioerê" in text.lower() else "Quarto Centenário"
                    db.atualizar_status(lado, "FECHADO")
                    outro = "Goioerê" if lado == "Quarto Centenário" else "Quarto Centenário"
                    db.atualizar_status(outro, "LIBERADO")
                    
                    msg = f"⚠️ ATENÇÃO ⚠️\n\n🔴 {lado}: FECHADO\n🟢 {outro}: LIBERADO"
                    requests.post(
                        f"{os.getenv('SERVER_URL')}/message/sendText/{os.getenv('INSTANCE')}",
                        json={"number": group_id, "text": msg},
                        headers={"apikey": os.getenv('APIKEY')}
                    )
        
        return jsonify({"status": True}), 200
    except:
        return jsonify({"status": False}), 500

# Inicialização simples
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=int(os.getenv('PORT', 80))) 