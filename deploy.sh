#!/bin/bash

# Configurações
SERVER="seu-usuario@seu-servidor"
REMOTE_PATH="/caminho/no/servidor"
SERVICE_NAME="seu-servico"

# Deploy
echo "Iniciando deploy..."
git add .
git commit -m "Update files"
git push

ssh $SERVER << EOF
    cd $REMOTE_PATH
    git pull
    systemctl restart $SERVICE_NAME
    echo "Deploy concluído!"
EOF 