import requests
import os
from datetime import datetime, timezone, timedelta

token =  os.getenv('pandascore_api_token')

def make_request(url): 
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return f"Erro na requisição: {e}"

def get_furia_lineup(time=None):
    url = f'https://api.pandascore.co/teams?filter[slug]=furia'
    data = make_request(url)

    if data:
        players = data[0].get('players', [])
        if players:
            return "\n".join(f"● {player['name']}" for player in players)
        return "Jogadores não encontrados."
    return "Time não encontrado."

def get_furia_last_game(time=None):
    url = f'https://api.pandascore.co/csgo/matches/past?filter[opponent_id]=furia'
    data = make_request(url)

    if data:
        match = data[0]
        return (
            f"<b>{match.get('name')}</b>\n"
            f"<b>Campeonato:</b> {match.get('league', {}).get('name')}\n"
            f"<b>Vencedor:</b> {match.get('winner', {}).get('name', 'Sem vencedor')}"
        )
    return "Nenhuma partida passada encontrada."

def get_furia_next_game(time=None):
    url = f'https://api.pandascore.co/csgo/matches/upcoming?filter[opponent_id]=furia'
    data = make_request(url)

    if data:
        match = data[0]
        match_name = match.get('name')
        match_datetime = match.get('begin_at')

        if match_datetime:
            try:
                dt_utc = datetime.strptime(match_datetime, "%Y-%m-%dT%H:%M:%SZ")
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)

                brazil_tz = timezone(timedelta(hours=-3))
                dt_brazil = dt_utc.astimezone(brazil_tz)

                formatted_date = dt_brazil.strftime("%d/%m/%Y às %H:%M")
            except ValueError:
                formatted_date = match_datetime
        else:
            formatted_date = "Data não definida"

        return (
            f"<b>{match_name}</b>\n"
            f"<b>Campeonato:</b> {match.get('league', {}).get('name')}\n"
            f"<b>Data e Hora:</b> {formatted_date}"
        )
    return "A próxima partida da FURIA ainda não foi marcada."