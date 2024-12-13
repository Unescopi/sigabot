import os
import sys
import logging
import random
import requests
from datetime import datetime, timedelta
from database import (
    get_status, update_status, record_closure_time, calculate_average_closure,
    get_daily_stats, get_weather_status, update_weather
)
from config import (
    BR_TIMEZONE, PICOS, ALERTA_TEMPO_MEDIO, WEATHER_API_KEY,
    CITY_ID, WEATHER_UPDATE_INTERVAL
)

logger = logging.getLogger(__name__)

# Controle de publicidade
ultima_publicidade = None
INTERVALO_MINIMO_PUBLICIDADE = timedelta(minutes=30)

# Controle de tempo entre atualizações
ultima_atualizacao_center = None
ultima_atualizacao_goio = None
INTERVALO_MINIMO_ATUALIZACAO = timedelta(minutes=2)  # 2 minutos entre atualizações

def get_current_time():
    """Retorna a hora atual no fuso horário do Brasil"""
    return datetime.now(BR_TIMEZONE)

def is_horario_pico():
    """Verifica se é horário de pico"""
    hora_atual = get_current_time().hour
    return any(
        inicio <= hora_atual <= fim 
        for inicio, fim in PICOS.values()
    )

def check_long_closure(lado, tempo_fechado):
    """Verifica se o fechamento está mais longo que o normal"""
    media = calculate_average_closure(lado)
    if media > 0 and tempo_fechado > (media * ALERTA_TEMPO_MEDIO):
        return (
            f"⚠️ *Alerta de Fechamento Longo*\n"
            f"Tempo atual: {tempo_fechado} minutos\n"
            f"Média normal: {media} minutos"
        )
    return None

def update_weather_info():
    """Atualiza informações do clima via API"""
    if not WEATHER_API_KEY:
        return None
        
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&appid={WEATHER_API_KEY}&units=metric&lang=pt_br"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            condicao = data['weather'][0]['description']
            temp = data['main']['temp']
            
            # Gera alertas baseados nas condições
            alerta = None
            if 'rain' in data or 'thunderstorm' in data:
                alerta = "🌧️ Chuva na região - Dirija com cuidado!"
            elif temp > 35:
                alerta = "🌡️ Temperatura muito alta - Hidrate-se!"
            
            update_weather(condicao, alerta)
            return {'condicao': condicao, 'alerta': alerta}
            
    except Exception as e:
        logger.error(f"Erro ao atualizar clima: {e}")
    return None

def get_status_message(lado, status, ultima_atualizacao):
    """Gera mensagem detalhada sobre o status"""
    lado_formatado = "Quarto Centenário" if lado == "CENTER" else "Goioerê"
    tempo_desde = get_time_since_update(ultima_atualizacao)
    
    if status == 'FECHADO':
        tempo_medio = calculate_average_closure(lado)
        mensagem = (
            f"🚫 O lado de *{lado_formatado}* está *FECHADO*\n"
            f"⏱ Tempo médio de espera: {tempo_medio} minutos\n"
            f"📊 Baseado nos últimos 5 fechamentos\n"
            f"🕒 Última atualização: {ultima_atualizacao} ({tempo_desde})"
        )
        
        # Adiciona alerta de horário de pico se necessário
        if is_horario_pico():
            mensagem += "\n⚠️ *Atenção*: Horário de pico!"
            
        # Adiciona alerta de clima se houver
        weather = get_weather_status()
        if weather and weather.get('alerta'):
            mensagem += f"\n{weather['alerta']}"
            
        return mensagem
    
    return (
        f"✅ O lado de *{lado_formatado}* está *LIBERADO*\n"
        f"🕒 Atualizado: {ultima_atualizacao} ({tempo_desde})"
    )

def get_mensagem_ajuda():
    """Retorna a mensagem de ajuda com instruções do bot"""
    return (
        "🤖 *BOT SIGUE E PARE*\n\n"
        "*Comandos disponíveis:*\n"
        "!center - Alterna status de Quarto Centenário\n"
        "!goio - Alterna status de Goioerê\n"
        "!status - Mostra status dos dois lados\n"
        "!stats - Mostra estatísticas do dia\n"
        "!pico - Informações sobre horários de pico\n"
        "!ajuda - Mostra esta mensagem\n\n"
        "*Linguagem Natural:*\n"
        "- Como está o lado de Goioerê?\n"
        "- Liberou Quarto Centenário\n"
        "- Fechou o lado de Goioerê\n"
        "- Qual a situação dos dois lados?\n\n"
        "📱 O bot atualiza automaticamente o status quando alguém informa no grupo.\n"
        "⏱ Também calcula o tempo médio de espera em cada lado."
    )

def get_stats_message():
    """Retorna mensagem com estatísticas do dia"""
    stats = get_daily_stats()
    return (
        "📊 *Estatísticas do Dia*\n\n"
        f"• Total de fechamentos: {stats['total_fechamentos']}\n"
        f"• Tempo médio fechado: {stats['tempo_medio']} minutos\n"
        f"• Horário mais movimentado: {stats['horario_pico']}\n\n"
        "ℹ️ Baseado nos registros de hoje"
    )

def get_pico_message():
    """Retorna mensagem sobre horários de pico"""
    return (
        "⏰ *Horários de Maior Movimento*\n\n"
        "🌅 *Manhã:* 06:00 - 08:00\n"
        "🌞 *Almoço:* 11:00 - 13:00\n"
        "🌇 *Tarde:* 17:00 - 19:00\n\n"
        "ℹ️ Nesses horários o tempo de espera pode ser maior"
    )

def get_mensagem_publicidade():
    mensagens = [
        "☕ *Parada obrigatória no PRADO CAFÉ*\n"
        "📍 Quarto Centenário - PR\n\n"
        "• Café fresquinho\n"
        "• Salgados na hora\n"
        "• Ambiente climatizado\n\n"
        "📱 Pedidos: (44) 9164-7725\n"
        "📸 @prado_cafee",
        
        "🥐 *PRADO CAFÉ - Seu point em QC*\n\n"
        "• Cafés especiais\n"
        "• Doces artesanais\n"
        "• Lanches deliciosos\n\n"
        "📱 Delivery: (44) 9164-7725\n"
        "📍 Quarto Centenário",
        
        "⏰ *Hora do café no PRADO CAFÉ!*\n\n"
        "• Café premium\n"
        "• Bolos caseiros\n"
        "• Ambiente família\n\n"
        "📱 Peça já: (44) 9164-7725\n"
        "📍 Centro - Quarto Centenário",
        
        "🌟 *PRADO CAFÉ te espera!*\n\n"
        "• Café na hora\n"
        "• Salgados frescos\n"
        "• Wi-Fi grátis\n\n"
        "📱 Fale conosco: (44) 9164-7725\n"
        "📍 Quarto Centenário - PR"
    ]
    return random.choice(mensagens)

def process_message(data):
    """Processa a mensagem recebida e retorna a resposta"""
    try:
        mensagem = data.get('text', '').lower()
        nome_remetente = data.get('sender', {}).get('pushName', 'Usuário')
        numero_remetente = data.get('sender', {}).get('id', '').split('@')[0]
        
        # Comandos especiais de admin
        if numero_remetente == os.getenv('ADMIN_NUMBER'):
            if mensagem == '!stop':
                logger.info("Comando de parada recebido do admin")
                os._exit(0)  # Para o bot imediatamente
            elif mensagem == '!start':
                logger.info("Comando de reinício recebido do admin")
                os.execv(sys.executable, ['python'] + sys.argv)  # Reinicia o bot
                
        logger.info(f"=== PROCESSANDO MENSAGEM ===")
        logger.info(f"Texto: {mensagem}")
        logger.info(f"Remetente: {nome_remetente}")
        logger.info(f"Hora atual: {get_current_time().strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("===========================")
        
        # Atualiza informações do clima periodicamente
        update_weather_info()
        
        # Lista de comandos válidos
        comandos_validos = ['!center', '!goio', '!status', '!stats', '!pico', '!ajuda']
        
        # Se começa com ! mas não é um comando válido, ignora
        if mensagem.startswith('!') and mensagem not in comandos_validos:
            return None
            
        # Se é um comando válido, processa
        if mensagem in comandos_validos:
            logger.info("Processando comando")
            response = process_command(mensagem, nome_remetente)
            logger.info(f"Resposta do comando: {response}")
            return response
            
        logger.info("Processando linguagem natural")
        return process_natural_language(mensagem, nome_remetente)
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        logger.error(f"Detalhes do erro: {e.__class__.__name__}")
        logger.error(f"Dados recebidos: {data}")
        
        if isinstance(e, ValueError):
            return "❌ Erro ao processar valores na mensagem"
        elif isinstance(e, KeyError):
            return "❌ Erro ao acessar dados da mensagem"
        elif isinstance(e, TypeError):
            return "❌ Erro no tipo de dados da mensagem"
        else:
            return "❌ Ocorreu um erro ao processar sua mensagem"

def process_command(mensagem, nome_remetente):
    """Processa comandos específicos (!status, !center, !goio, etc)"""
    try:
        global ultima_atualizacao_center, ultima_atualizacao_goio
        
        logger.info(f"Iniciando processamento do comando: {mensagem}")
        
        # Comandos de informação
        if mensagem == '!ajuda':
            return get_mensagem_ajuda()
        elif mensagem == '!stats':
            return get_stats_message()
        elif mensagem == '!pico':
            return get_pico_message()
            
        # Se for comando !status, mostra status dos dois lados
        if mensagem == '!status':
            status_center, ultima_center = get_status('CENTER')
            status_goio, ultima_goio = get_status('GOIO')
            
            # Garante que não estejam fechados ao mesmo tempo
            if status_center == 'FECHADO' and status_goio == 'FECHADO':
                logger.warning("Detectado ambos os lados fechados, corrigindo...")
                update_status('GOIO', 'ABERTO')
                status_goio = 'ABERTO'
            
            # Gera mensagens detalhadas para cada lado
            msg_center = get_status_message('CENTER', status_center, ultima_center)
            msg_goio = get_status_message('GOIO', status_goio, ultima_goio)
            
            resposta = f"{msg_center}\n\n{msg_goio}"
            
            # Adiciona propaganda se possível
            if pode_enviar_publicidade():
                resposta += f"\n\n{get_mensagem_publicidade()}"
                
            return resposta
            
        # Comandos de alteração de status
        lado_atual = 'CENTER' if mensagem == '!center' else 'GOIO'
        
        # Verifica se pode atualizar
        if not pode_atualizar_lado(lado_atual):
            return None
            
        lado_oposto = 'GOIO' if mensagem == '!center' else 'CENTER'
        
        status_atual, ultima_atualizacao = get_status(lado_atual)
        status_oposto, _ = get_status(lado_oposto)
        
        novo_status = 'ABERTO' if status_atual == 'FECHADO' else 'FECHADO'
        logger.info(f"Novo status será: {novo_status}")
        
        # Se vai fechar um lado, garante que o outro esteja aberto
        if novo_status == 'FECHADO' and status_oposto == 'FECHADO':
            logger.info(f"Abrindo lado oposto para evitar ambos fechados")
            update_status(lado_oposto, 'ABERTO')
            
        # Se vai abrir um lado, fecha o outro
        elif novo_status == 'ABERTO':
            logger.info(f"Fechando lado oposto: {lado_oposto}")
            update_status(lado_oposto, 'FECHADO')
            
        # Calcula o tempo de fechamento se estiver abrindo
        if status_atual == 'FECHADO':
            try:
                ultima = datetime.strptime(ultima_atualizacao, '%d/%m/%Y %H:%M')
                ultima = BR_TIMEZONE.localize(ultima)
                tempo_fechamento = int((get_current_time() - ultima).total_seconds() / 60)
                record_closure_time(lado_atual, tempo_fechamento)
                
                # Verifica se o fechamento foi mais longo que o normal
                alerta_tempo = check_long_closure(lado_atual, tempo_fechamento)
            except Exception as e:
                logger.error(f"Erro ao calcular tempo de fechamento: {e}")
            
        # Atualiza o status
        update_status(lado_atual, novo_status)
        
        # Atualiza o timestamp da última atualização
        update_timestamps(lado_atual)
        
        # Gera mensagem de resposta
        msg_atual = get_status_message(lado_atual, novo_status, get_current_time().strftime('%d/%m/%Y %H:%M'))
        msg_oposto = get_status_message(lado_oposto, 'FECHADO' if novo_status == 'ABERTO' else 'ABERTO', 
                                      get_current_time().strftime('%d/%m/%Y %H:%M'))
        
        resposta = (
            f"✅ Status atualizado por {nome_remetente}\n\n"
            f"{msg_atual}\n\n{msg_oposto}"
        )
        
        # Adiciona alerta de tempo longo se houver
        if 'alerta_tempo' in locals() and alerta_tempo:
            resposta += f"\n\n{alerta_tempo}"
            
        # Adiciona propaganda se possível
        if pode_enviar_publicidade():
            resposta += f"\n\n{get_mensagem_publicidade()}"
            
        return resposta
        
    except Exception as e:
        logger.error(f"Erro ao processar comando: {str(e)}")
        logger.error(f"Detalhes do erro: {e.__class__.__name__}")
        return "❌ Erro ao atualizar status"

def process_natural_language(mensagem, nome_remetente):
    """Processa mensagens em linguagem natural"""
    try:
        logger.info(f"=== PROCESSANDO LINGUAGEM NATURAL ===")
        logger.info(f"Mensagem original: {mensagem}")
        logger.info(f"Remetente: {nome_remetente}")
        
        # Palavras-chave para reconhecimento
        palavras_chave_center = [
            'quarto centenario', 'quarto centenário', 'center', '4º', '4', 'quarto', 
            'centenario', 'centenário', '4 centenario', 'centro', 'qc', 'quarto c',
            'qcentenario', 'q.c.', 'q c', '4c', '4 c', 'centenário'
        ]
        
        palavras_chave_goio = [
            'goioere', 'goioerê', 'goio', 'goiô', 'goiere', 'goiêre', 'goioere', 
            'goioerê', 'goiore', 'goyo', 'goió', 'goiô', 'goiere', 'goiêre'
        ]
        
        # Palavras que indicam uma atualização real
        palavras_comando_abertura = [
            'liberou', 'abriu', 'passou', 'fluindo', 'andando', 'livre',
            'liberado', 'flow', 'normal', 'normalizado', 'ok', 'tranquilo',
            'passando', 'movimentando', 'seguindo', 'desembargou', 'destravou'
        ]
        palavras_comando_fechamento = [
            'fechou', 'parou', 'trava', 'travou', 'retido', 'congestionado',
            'parado', 'trancado', 'bloqueado', 'interditado', 'lento',
            'congestionamento', 'fila', 'retenção', 'retencao', 'embargou'
        ]
        
        # Identifica o lado
        lado = None
        for palavra in palavras_chave_center:
            if palavra in mensagem.lower():
                lado = 'CENTER'
                logger.info(f"Lado identificado como CENTER pela palavra '{palavra}'")
                break
        for palavra in palavras_chave_goio:
            if palavra in mensagem.lower():
                lado = 'GOIO'
                logger.info(f"Lado identificado como GOIO pela palavra '{palavra}'")
                break
                
        if not lado:
            logger.info("Nenhum lado identificado na mensagem")
            return None
            
        lado_formatado = "Quarto Centenário" if lado == "CENTER" else "Goioerê"
        lado_oposto = "GOIO" if lado == "CENTER" else "CENTER"
        lado_oposto_formatado = "Goioerê" if lado == "CENTER" else "Quarto Centenário"
        
        # Se a mensagem termina com '?', é uma pergunta
        if mensagem.strip().endswith('?'):
            status_atual, ultima_atualizacao = get_status(lado)
            return get_status_message(lado, status_atual, ultima_atualizacao)
            
        # Verifica se pode atualizar
        if not pode_atualizar_lado(lado):
            return None
            
        # Se tem palavra de comando de abertura
        if any(palavra in mensagem for palavra in palavras_comando_abertura):
            status_atual, ultima_atualizacao = get_status(lado)
            if status_atual == 'ABERTO':
                return f"ℹ️ O lado de *{lado_formatado}* já está *ABERTO*"
                
            # Se estava fechado, registra o tempo
            try:
                ultima = datetime.strptime(ultima_atualizacao, '%d/%m/%Y %H:%M')
                ultima = BR_TIMEZONE.localize(ultima)
                tempo_fechamento = int((get_current_time() - ultima).total_seconds() / 60)
                record_closure_time(lado, tempo_fechamento)
            except Exception as e:
                logger.error(f"Erro ao calcular tempo de fechamento: {e}")
                
            # Abre este lado e fecha o outro
            update_status(lado, 'ABERTO')
            update_status(lado_oposto, 'FECHADO')
            
            # Atualiza timestamp
            update_timestamps(lado)
                
            return (
                f"✅ Status atualizado por {nome_remetente}\n\n"
                f"📍 {lado_formatado}: *ABERTO*\n"
                f"📍 {lado_oposto_formatado}: *FECHADO*"
            )
            
        # Se tem palavra de comando de fechamento
        if any(palavra in mensagem for palavra in palavras_comando_fechamento):
            status_atual, ultima_atualizacao = get_status(lado)
            if status_atual == 'FECHADO':
                return f"ℹ️ O lado de *{lado_formatado}* já está *FECHADO*"
                
            # Fecha este lado e abre o outro
            update_status(lado, 'FECHADO')
            update_status(lado_oposto, 'ABERTO')
            
            # Atualiza timestamp
            update_timestamps(lado)
                
            return (
                f"✅ Status atualizado por {nome_remetente}\n\n"
                f"📍 {lado_formatado}: *FECHADO*\n"
                f"📍 {lado_oposto_formatado}: *ABERTO*"
            )
            
        # Se não é pergunta nem comando, apenas mostra o status
        status_atual, ultima_atualizacao = get_status(lado)
        resposta = get_status_message(lado, status_atual, ultima_atualizacao)
        
        logger.info(f"Status atual: {status_atual}")
        logger.info(f"Última atualização: {ultima_atualizacao}")
        logger.info(f"Resposta gerada: {resposta}")
        logger.info("================================")
        
        return resposta
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return "❌ Ocorreu um erro ao processar sua mensagem"

def get_time_since_update(ultima_atualizacao):
    """Calcula o tempo desde a última atualização"""
    agora = get_current_time()
    ultima = datetime.strptime(ultima_atualizacao, '%d/%m/%Y %H:%M')
    ultima = BR_TIMEZONE.localize(ultima)
    
    diff = agora - ultima
    minutos = int(diff.total_seconds() / 60)
    
    if minutos < 60:
        return f"{minutos} minutos atrás"
    elif minutos < 1440:  # menos de 24 horas
        horas = minutos // 60
        return f"{horas} horas atrás"
    else:
        dias = minutos // 1440
        return f"{dias} dias atrás"

def pode_enviar_publicidade():
    """Verifica se pode enviar publicidade baseado em tempo e chance"""
    global ultima_publicidade
    agora = get_current_time()
    
    # Se é a primeira execução ou passou o tempo mínimo
    if ultima_publicidade is None or (agora - ultima_publicidade) >= INTERVALO_MINIMO_PUBLICIDADE:
        # 50% de chance de mostrar propaganda
        if random.random() < 0.5:  
            logger.info("Propaganda autorizada")
            ultima_publicidade = agora
            return True
        else:
            logger.info("Propaganda não selecionada no sorteio")
    else:
        logger.info(f"Muito cedo para nova propaganda. Última foi há {agora - ultima_publicidade}")
    return False

def pode_atualizar_lado(lado):
    """Verifica se já passou tempo suficiente desde a última atualização"""
    global ultima_atualizacao_center, ultima_atualizacao_goio
    
    agora = get_current_time()
    ultima = ultima_atualizacao_center if lado == 'CENTER' else ultima_atualizacao_goio
    
    if ultima is None:
        return True
        
    return (agora - ultima) >= INTERVALO_MINIMO_ATUALIZACAO

def update_timestamps(lado):
    """Função centralizada para atualizar timestamps"""
    global ultima_atualizacao_center, ultima_atualizacao_goio
    if lado == 'CENTER':
        ultima_atualizacao_center = get_current_time()
    else:
        ultima_atualizacao_goio = get_current_time()

def alternar_lados(lado_atual, novo_status, nome_remetente):
    """Função centralizada para alternar status dos lados"""
    lado_oposto = 'GOIO' if lado_atual == 'CENTER' else 'CENTER'
    
    # Se vai fechar um lado, garante que o outro esteja aberto
    if novo_status == 'FECHADO':
        status_oposto, _ = get_status(lado_oposto)
        if status_oposto == 'FECHADO':
            update_status(lado_oposto, 'ABERTO')
            update_timestamps(lado_oposto)
    
    # Se vai abrir um lado, fecha o outro
    elif novo_status == 'ABERTO':
        update_status(lado_oposto, 'FECHADO')
        update_timestamps(lado_oposto)
    
    # Atualiza o lado atual
    update_status(lado_atual, novo_status)
    update_timestamps(lado_atual)
    
    # Retorna mensagem formatada
    lado_formatado = "Quarto Centenário" if lado_atual == "CENTER" else "Goioerê"
    lado_oposto_formatado = "Goioerê" if lado_atual == "CENTER" else "Quarto Centenário"
    
    return (
        f"✅ Status atualizado por {nome_remetente}\n\n"
        f"📍 {lado_formatado}: *{novo_status}*\n"
        f"📍 {lado_oposto_formatado}: *{'FECHADO' if novo_status == 'ABERTO' else 'ABERTO'}*"
    )