require('dotenv').config();
const express = require('express');
const db = require('./src/database');
const whatsapp = require('./src/whatsapp');
const app = express();

// Middleware
app.use(express.json());

// Rota de teste
app.get('/', (req, res) => {
    res.json({
        status: 'online',
        message: 'Bot está funcionando!'
    });
});

// Rota de teste com variáveis
app.get('/test', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Endpoint de teste funcionando',
        env_test: process.env.GROUP_TEST_ID
    });
});

// Webhook
app.post('/webhook', async (req, res) => {
    try {
        const data = req.body;
        console.log('Webhook recebido:', data);

        if (data?.event === 'messages.upsert') {
            const message = data.data || {};
            const groupId = message.key?.remoteJid;
            const text = message.message?.conversation;

            if (text && [process.env.GROUP_ID, process.env.GROUP_TEST_ID].includes(groupId)) {
                if (text.toLowerCase().includes('fechado')) {
                    const lado = text.toLowerCase().includes('goioerê') ? 'Goioerê' : 'Quarto Centenário';
                    const outro = lado === 'Goioerê' ? 'Quarto Centenário' : 'Goioerê';

                    // Atualiza status
                    await db.updateStatus(lado, 'FECHADO');
                    await db.updateStatus(outro, 'LIBERADO');

                    // Envia mensagem
                    const msg = `⚠️ ATENÇÃO ⚠️\n\n🔴 ${lado}: FECHADO\n🟢 ${outro}: LIBERADO`;
                    await whatsapp.sendMessage(groupId, msg);
                    console.log('Mensagem enviada');
                }
                
                // Comando de status
                if (text.toLowerCase().includes('status')) {
                    const goioere = await db.getLastStatus('Goioerê');
                    const quarto = await db.getLastStatus('Quarto Centenário');
                    
                    const msg = `📊 Status Atual:\n\n${goioere === 'FECHADO' ? '🔴' : '🟢'} Goioerê: ${goioere}\n${quarto === 'FECHADO' ? '🔴' : '🟢'} Quarto Centenário: ${quarto}`;
                    await whatsapp.sendMessage(groupId, msg);
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