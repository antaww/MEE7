import os
import requests
from discord.ext import tasks
from dotenv import load_dotenv

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", ".env"))
load_dotenv(dotenv_path)

# Charger les variables d'environnement depuis le fichier .env
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
    print(
        "Les variables d'environnement TWITCH_CLIENT_ID ou TWITCH_CLIENT_SECRET ne sont pas configurées correctement.")
    exit()


# Fonction pour obtenir un jeton d'accès
def get_access_token(client_id, client_secret):
    url = 'https://id.twitch.tv/oauth2/token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


# Obtenir le jeton d'accès
TWITCH_ACCESS_TOKEN = get_access_token(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)

# Liste des streamers à surveiller
STREAMERS = ["nikof", "alphacast", "fugu_fps"]

# URL de l'API Twitch
API_URL = 'https://api.twitch.tv/helix/streams'

# En-têtes pour l'API Twitch
API_HEADERS = {
    'Client-ID': TWITCH_CLIENT_ID,
    'Authorization': 'Bearer ' + TWITCH_ACCESS_TOKEN,
}

# Dictionnaire pour stocker l'état en ligne des streamers
streamers_status = {streamer: False for streamer in STREAMERS}


@tasks.loop(minutes=1)
async def check_streamers(bot):
    print("Checking streamers...")
    for streamer in STREAMERS:
        is_online = await check_user(streamer)
        if is_online and not streamers_status[streamer]:
            streamers_status[streamer] = True
            await notify_discord(streamer, bot)
        elif not is_online and streamers_status[streamer]:
            streamers_status[streamer] = False


async def check_user(streamer):
    url = f'{API_URL}?user_login={streamer}'
    try:
        req = requests.get(url, headers=API_HEADERS)
        json_data = req.json()
        if json_data.get('data'):
            return True
        else:
            return False
    except Exception as e:
        print("Error checking user:", e)
        return False


async def notify_discord(streamer, bot):
    # Remplacez 1234567890 par l'ID de votre canal Discord où vous souhaitez envoyer les notifications
    channel_id = 1252372530736664586
    bot_channel = bot.get_channel(channel_id)
    if bot_channel:
        await bot_channel.send(
            f"{streamer} a commencé un stream sur Twitch ! 🎉\nRegardez ici : https://www.twitch.tv/{streamer}"
        )
