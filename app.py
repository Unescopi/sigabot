from flask import Flask, request, jsonify
import os
import logging
import requests
from waitress import serve
from dotenv import load_dotenv
import sqlite3

# Configuração básica
load_dotenv()
app = Flask(__name__)

# Banco de dados
def init_db():
    with sqlite3.connect('/app/data/status.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lado TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def update_status(lado, status):
    with sqlite3.connect('/app/data/status.db') as conn:
        conn.execute('INSERT INTO status_history (lado, status) VALUES (?, ?)', (lado, status))

# Rotas
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print('Webhook recebido:', data)
        
        if data and data.get('event') == 'messages.upsert':
            message = data.get('data', {})
            group_id = message.get('key', {}).get('remoteJid')
            text = message.get('message', {}).get('conversation', '')
            
            if text and group_id in [os.getenv('GROUP_ID'), os.getenv('GROUP_TEST_ID')]:
                if 'fechado' in text.lower():
                    lado = 'Goioerê' if 'goioerê' in text.lower() else 'Quarto Centenário'
                    outro = 'Goioerê' if lado == 'Quarto Centenário' else 'Quarto Centenário'
                    
                    update_status(lado, 'FECHADO')
                    update_status(outro, 'LIBERADO')
                    
                    msg = f'⚠️ ATENÇÃO ⚠️\n\n🔴 {lado}: FECHADO\n🟢 {outro}: LIBERADO'
                    
                    requests.post(
                        f"{os.getenv('SERVER_URL')}/message/sendText/{os.getenv('INSTANCE')}",
                        json={'number': group_id, 'text': msg},
                        headers={'apikey': os.getenv('APIKEY')}
                    )
        
        return jsonify({'status': True})
    except Exception as e:
        print('Erro:', str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    serve(app, host='0.0.0.0', port=int(os.getenv('PORT', 80))) 