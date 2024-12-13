require('dotenv').config();
const express = require('express');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const app = express();

// Configuração do banco
const db = new sqlite3.Database('/app/data/status.db');
db.run(`CREATE TABLE IF NOT EXISTS status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lado TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)`);

// Middleware
app.use(express.json());

// Webhook
app.post('/webhook', async (req, res) => {
    try {
        const data = req.body;
        console.log('Webhook recebido');

        if (data.event === 'messages.upsert') {
            const message = data.data || {};
            const groupId = message.key?.remoteJid;
            const text = message.message?.conversation;

            console.log(`Mensagem recebida: ${text}`);

            if (text && [process.env.GROUP_ID, process.env.GROUP_TEST_ID].includes(groupId)) {
                if (text.toLowerCase().includes('fechado')) {
                    const lado = text.toLowerCase().includes('goioerê') ? 'Goioerê' : 'Quarto Centenário';
                    const outro = lado === 'Goioerê' ? 'Quarto Centenário' : 'Goioerê';

                    // Atualiza status
                    db.run('INSERT INTO status_history (lado, status) VALUES (?, ?)', [lado, 'FECHADO']);
                    db.run('INSERT INTO status_history (lado, status) VALUES (?, ?)', [outro, 'LIBERADO']);

                    // Envia mensagem
                    const msg = `⚠️ ATENÇÃO ⚠️\n\n🔴 ${lado}: FECHADO\n🟢 ${outro}: LIBERADO`;
                    await axios.post(
                        `${process.env.SERVER_URL}/message/sendText/${process.env.INSTANCE}`,
                        {
                            number: groupId,
                            text: msg
                        },
                        {
                            headers: { apikey: process.env.APIKEY }
                        }
                    );
                    console.log('Mensagem enviada');
                }
            }
        }

        res.json({ status: true });
    } catch (error) {
        console.error('Erro:', error);
        res.status(500).json({ error: error.message });
    }
});

// Inicia servidor
const PORT = process.env.PORT || 80;
app.listen(PORT, () => {
    console.log(`Servidor rodando na porta ${PORT}`);
}); 