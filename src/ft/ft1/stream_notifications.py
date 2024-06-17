import os
import requests
from discord.ext import tasks
from dotenv import load_dotenv

from src.utilities.settings import Settings

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", ".env"))
load_dotenv(dotenv_path)
settings = Settings()

TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
    print(
        "Les variables d'environnement TWITCH_CLIENT_ID ou TWITCH_CLIENT_SECRET ne sont pas configurées correctement.")
    exit()


def get_access_token(client_id, client_secret):
    """
    This function retrieves an access token from Twitch's OAuth2 endpoint.

    It takes two arguments:
    - client_id: The client ID for the Twitch application.
    - client_secret: The client secret for the Twitch application.

    The function first constructs the URL for the OAuth2 endpoint and the payload for the request.
    The payload includes the client_id, client_secret, and the grant_type which is set to 'client_credentials'.
    It then sends a POST request to the OAuth2 endpoint with the payload.

    If the request is successful, it retrieves the access token from the response and returns it.
    If the request is not successful, it raises an HTTPError.

    This function returns a string which is the access token.
    """
    url = 'https://id.twitch.tv/oauth2/token'  # The URL for the OAuth2 endpoint.
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)  # Send a POST request to the OAuth2 endpoint with the payload.
    response.raise_for_status()  # If the request is not successful, raise an HTTPError.
    return response.json()['access_token']  # Retrieve the access token from the response and return it.


TWITCH_ACCESS_TOKEN = get_access_token(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)

# List of streamers to check
STREAMERS = ["nikof", "alphacast", "fugu_fps"]

# Twitch API URL
API_URL = 'https://api.twitch.tv/helix/streams'

# Twitch API headers
API_HEADERS = {
    'Client-ID': TWITCH_CLIENT_ID,
    'Authorization': 'Bearer ' + TWITCH_ACCESS_TOKEN,
}

# Dictionary to store the status of each streamer
streamers_status = {streamer: False for streamer in STREAMERS}


@tasks.loop(minutes=1)
async def check_streamers(bot):
    """
    This function is a task that runs every minute. Its purpose is to check the status of a list of streamers.

    It takes one argument:
    - bot: The bot instance.

    The function first prints a message to the console indicating that it's checking the streamers. It then iterates
    over the list of streamers and checks if each streamer is online by calling the `check_user` function. If a
    streamer is online and was previously not online, it updates the streamer's status to online and sends a
    notification to Discord by calling the `notify_discord` function. If a streamer is not online and was previously
    online, it updates the streamer's status to offline.

    This function doesn't return anything.
    """
    print("Checking streamers...")
    for streamer in STREAMERS:
        is_online = await check_user(streamer)  # Check if the streamer is online by calling the `check_user` function.
        if is_online and not streamers_status[streamer]:  # If the streamer is online and was previously not online.
            streamers_status[streamer] = True  # Update the streamer's status to online.
            await notify_discord(streamer, bot)  # Send a notification to Discord by calling the `notify_discord` function.
        elif not is_online and streamers_status[streamer]:  # If the streamer is not online and was previously online.
            streamers_status[streamer] = False  # Update the streamer's status to offline.


async def check_user(streamer):
    """
    This function checks if a given streamer is currently online on Twitch.

    It takes one argument:
    - streamer: The username of the streamer to check.

    The function first constructs the URL for the Twitch API endpoint to get the stream information for the streamer.
    It then sends a GET request to the Twitch API endpoint with the API headers.

    If the request is successful, it retrieves the data from the response and checks if there is any data.
    If there is data, it means the streamer is online and the function returns True.
    If there is no data, it means the streamer is not online and the function returns False.

    If the request is not successful or an exception occurs, it prints an error message to the console and returns False.

    This function returns a boolean indicating whether the streamer is online or not.
    """
    url = f'{API_URL}?user_login={streamer}'  # Construct the URL for the Twitch API endpoint.
    try:
        req = requests.get(url, headers=API_HEADERS)  # Send a GET request to the Twitch API endpoint with the API headers.
        json_data = req.json()  # Retrieve the data from the response.
        if json_data.get('data'):  # If there is any data, the streamer is online.
            return True
        else:
            return False
    except Exception as e:
        print("Error checking user:", e)
        return False


async def notify_discord(streamer, bot):
    """
    This function sends a notification to a specific Discord channel when a streamer starts streaming on Twitch.

    It takes two arguments:
    - streamer: The username of the streamer who started streaming.
    - bot: The bot instance.

    The function first retrieves the bot channel using the channel_id.
    If the bot channel exists, it sends a message to the channel with the streamer's name and a link to their Twitch stream.

    This function doesn't return anything.
    """
    channel_id = settings.get('twitch_channel_id')  # The ID of the Discord channel to send the notification to.
    bot_channel = bot.get_channel(channel_id)
    if bot_channel:  # If the bot channel exists.
        await bot_channel.send(
            f"> :tada: **{streamer}** started streaming on Twitch!\n"
            f"> :arrow_right_hook: Watch here: https://www.twitch.tv/{streamer}"
        )
