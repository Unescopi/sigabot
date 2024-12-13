const axios = require('axios');

class WhatsAppService {
    constructor() {
        this.baseUrl = process.env.SERVER_URL;
        this.instance = process.env.INSTANCE;
        this.apiKey = process.env.APIKEY;
    }

    async sendMessage(groupId, text) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/message/sendText/${this.instance}`,
                {
                    number: groupId,
                    text: text,
                    options: {
                        delay: 1200,
                        presence: "composing"
                    }
                },
                {
                    headers: { apikey: this.apiKey }
                }
            );
            return response.data;
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            throw error;
        }
    }
}

module.exports = new WhatsAppService(); 