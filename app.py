from flask import Flask, request, jsonify
import os
import logging
from services.evolution_service import process_message
import requests
from waitress import serve
from dotenv import load_dotenv
from services.database import Database
import sys

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração de logs mais simples
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Adicionar um log de teste na inicialização
print("=== INICIANDO BOT ===")
sys.stdout.flush()

# Logs iniciais
logger.info("=== INICIANDO SERVIDOR ===")
logger.info(f"Versão do Python: {sys.version}")
logger.info(f"Diretório atual: {os.getcwd()}")
logger.info(f"Variáveis de ambiente carregadas: {list(os.environ.keys())}")

# Inicializar conexão com banco de dados
db = Database()

app = Flask(__name__)

# Rota raiz para verificar se o servidor está online
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Bot está funcionando!"
    })

# Rota webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        logger.info("\n=== NOVA REQUISIÇÃO RECEBIDA ===")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Dados completos: {data}")
        
        if data.get('event') == 'messages.upsert':
            message_data = data.get('data', {})
            group_id = message_data.get('key', {}).get('remoteJid')
            
            if message_data.get('messageType') == 'conversation':
                text = message_data.get('message', {}).get('conversation')
                sender = message_data.get('pushName')
                
                if text and (group_id == os.getenv('GROUP_ID') or group_id == os.getenv('GROUP_TEST_ID')):
                    # Processar comandos de status
                    if "fechado" in text.lower():
                        lado = "Goioerê" if "goioerê" in text.lower() else "Quarto Centenário"
                        # Atualiza status do lado mencionado para FECHADO
                        db.atualizar_status(lado, "FECHADO")
                        # Atualiza o outro lado para LIBERADO
                        outro_lado = "Goioerê" if lado == "Quarto Centenário" else "Quarto Centenário"
                        db.atualizar_status(outro_lado, "LIBERADO")
                        
                        mensagem = f"⚠️ ATENÇÃO ⚠️\n\n"
                        mensagem += f"🔴 {lado}: FECHADO\n"
                        mensagem += f"🟢 {outro_lado}: LIBERADO"
                        
                        # Enviar mensagem
                        url = f"{data.get('server_url')}/message/sendText/{data.get('instance')}"
                        headers = {
                            "Content-Type": "application/json",
                            "apikey": data.get('apikey')
                        }
                        payload = {
                            "number": group_id,
                            "text": mensagem,
                            "options": {
                                "delay": 1200,
                                "presence": "composing"
                            }
                        }
                        response = requests.post(url, json=payload, headers=headers)
                        logger.info(f"Mensagem enviada: {response.status_code}")
                    else:
                        response = process_message({
                            'text': text,
                            'sender': {'pushName': sender}
                        })
                        
                        if response:
                            url = f"{data.get('server_url')}/message/sendText/{data.get('instance')}"
                            headers = {
                                "Content-Type": "application/json",
                                "apikey": data.get('apikey')
                            }
                            payload = {
                                "number": group_id,
                                "text": response,
                                "options": {
                                    "delay": 1200,
                                    "presence": "composing"
                                }
                            }
                            response = requests.post(url, json=payload, headers=headers)
                            logger.info(f"Mensagem enviada: {response.status_code}")
                
        return jsonify({"status": True}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    logger.info("Endpoint de teste acessado")
    return jsonify({
        "status": "ok",
        "message": "Endpoint de teste funcionando",
        "env_test": os.getenv('GROUP_TEST_ID')
    })

def start_server():
    try:
        port = int(os.getenv('PORT', 80))  # Porta 80 para HTTP
        logger.info(f"=== INICIANDO SERVIDOR NA PORTA {port} ===")
        serve(app, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        raise

if __name__ == '__main__':
    start_server() 