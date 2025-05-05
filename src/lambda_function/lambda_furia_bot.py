import json
import urllib.request
import boto3
import logging
import os

from furia_cs_data import get_furia_last_game, get_furia_next_game, get_furia_lineup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lex_client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body'])

            if 'message' in body:
                chat_id = body['message']['chat']['id']
                message = body['message']['text']

                lex_response = call_lex(chat_id, message)

                process_lex_response(chat_id, lex_response)
            else:
                logger.warning("'message' não encontrado no corpo")
        else:
            logger.warning("'body' não encontrado no evento")

        return {'statusCode': 200, 'body': json.dumps('Mensagem processada com sucesso')}

    except Exception as e:
        logger.error(f"Erro geral: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Erro interno')}


def call_lex(chat_id, message):
    try:
        bot_id = os.environ.get('bot_id')
        bot_alias_id = os.environ.get('bot_alias_id')

        response = lex_client.recognize_text(
            botId=bot_id,
            botAliasId=bot_alias_id,
            localeId='pt_BR',
            sessionId=str(chat_id),
            text=str(message)
        )

        return response

    except Exception as e:
        logger.error(f"Erro ao chamar Lex: {str(e)}")
        raise

def send_lex_messages(chat_id, response):
    for msg in response.get('messages', []):
        send_message(chat_id, msg.get('content', ''))

def get_team_from_slots(response):
    try:
        return response['sessionState']['intent']['slots']['TeamName']['value']['interpretedValue']
    except (TypeError, KeyError):
        return 'furia'

def send_message(chat_id, text):
    try:
        telegram_token = os.environ.get('telegram_token')
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        headers = {'Content-Type': 'application/json'}

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)

    except Exception as e:
        logger.error(f"Erro ao enviar mensagem para Telegram: {str(e)}")
        raise

def only_furia_response():
    return "Esse assunto aí não é comigo. O que realmente entendo é sobre a FURIA! 😎"

def handle_functionalities(chat_id, response):
    send_lex_messages(chat_id, response)
    msg = (
        "<b> Informações sobre o time FURIA de CS</b>\n"
        "✅ Próximo jogo\n"
        "✅ Último resultado\n"
        "✅ Elenco\n\n"
        "<b>Nossos links úteis:</b>\n"
        "<b>📌 Loja oficial:</b>\n"
        "<b>📌 Redes sociais:</b> \n\n"
        "<b>Quer saber mais sobre a FURIA?</b>\n"
        "❓ História da organização\n"
        "❓ Quem fundou a FURIA\n"
        "❓ Quando foi criada\n"
    )
    send_message(chat_id, msg)

def handle_last_game(chat_id, response):
    team = get_team_from_slots(response)

    if team.lower() == "furia":
        send_lex_messages(chat_id, response)
        msg = get_furia_last_game(team)
        send_message(chat_id, msg)
    else:
        msg = only_furia_response()
        send_message(chat_id, msg)

def handle_next_game(chat_id, response):
    team = get_team_from_slots(response)

    if team.lower() == "furia":
        send_lex_messages(chat_id, response)
        msg = get_furia_next_game(team)
        send_message(chat_id, msg)
    else:
        msg = only_furia_response()
        send_message(chat_id, msg)

def handle_lineup(chat_id, response):
    team = get_team_from_slots(response)

    if team.lower() == "furia":
        send_lex_messages(chat_id, response)
        msg = get_furia_lineup(team)
        send_message(chat_id, msg)
    else:
        msg = only_furia_response()
        send_message(chat_id, msg)

def handle_social_media(chat_id, response):
    send_lex_messages(chat_id, response)
    msg = (
        "<b>🔹 X:</b> <a href='https://x.com/FURIA'>@FURIA</a>\n"
        "<b>🔹 Instagram:</b> <a href='https://instagram.com/furiagg'>@furiagg</a>\n"
        "<b>🔹 YouTube:</b> <a href='https://www.youtube.com/@FURIAggCS'>FURIAggCS</a>"
    )
    send_message(chat_id, msg)

INTENT_HANDLERS = {
    'GreetingIntent': send_lex_messages,
    'FunctionalitiesIntent': handle_functionalities,
    'ExitIntent': send_lex_messages,
    'FoundersIntent': send_lex_messages,
    'FuriaHistoryIntent': send_lex_messages,
    'FuriaFoundationIntent': send_lex_messages,
    'FuriaStoreIntent': send_lex_messages,
    'FallbackIntent': send_lex_messages,
    'LastGameIntent': handle_last_game,
    'NextGameIntent': handle_next_game,
    'LineupIntent': handle_lineup,
    'SocialMediaIntent': handle_social_media,
}

def process_lex_response(chat_id, response):
    intent_name = response.get('sessionState', {}).get('intent', {}).get('name', 'indefinido')

    handler = INTENT_HANDLERS.get(intent_name)
    if handler:
        handler(chat_id, response)
    else:
        send_message(chat_id, "Desculpe, não entendi sua solicitação. Pode tentar reformular? 🤔")