import os

import discord
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
STREAMERS = settings.get('streamers_list')

# Twitch API URL
STREAMS_API_URL = 'https://api.twitch.tv/helix/streams'
USER_API_URL = 'https://api.twitch.tv/helix/users'

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
        datas = await check_user_and_get_info(
            streamer)  # Check if the streamer is online by calling the `check_user` function.
        is_online = bool(datas)
        # debug
        # print(f"{streamer} is online: {is_online} : {datas}")
        if is_online and not streamers_status[streamer]:  # If the streamer is online and was previously not online.
            streamers_status[streamer] = True  # Update the streamer's status to online.
            await notify_discord(datas, bot)  # Send a notification to Discord by calling the `notify_discord` function.
        elif not is_online and streamers_status[streamer]:  # If the streamer is not online and was previously online.
            streamers_status[streamer] = False  # Update the streamer's status to offline.


async def check_user_and_get_info(streamer):
    """
    This function checks if a given streamer is currently online on Twitch and if so, retrieves the user's information.

    Args:
        streamer (str): The username of the streamer to check.

    Returns:
        dict: A dictionary with the streamer's online status and user information if the streamer is online.
              If the streamer is not online, it returns an empty dictionary.

    The function first checks if the streamer is online by sending a GET request to the Twitch API endpoint.
    If there is any data in the response, the streamer is considered online and the function proceeds to retrieve the user's information.
    The user's information is retrieved by sending another GET request to the Twitch API endpoint, this time with the user_id obtained from the streamer's data.
    If there is any data in the response, the user's information is added to the return dictionary along with the streamer's data.
    If an exception occurs during the process, an error message is printed and an empty dictionary is returned.
    """
    url = f'{STREAMS_API_URL}?user_login={streamer}'  # Construct the URL for the Twitch API endpoint.
    try:
        req = requests.get(url,
                           headers=API_HEADERS)  # Send a GET request to the Twitch API endpoint with the API headers.
        json_data = req.json()  # Retrieve the data from the response.
        if json_data.get('data'):  # If there is any data, the streamer is online.
            streamer_data = json_data['data'][0]

            # Get user info
            user_id = streamer_data['user_id']
            url = f'{USER_API_URL}?id={user_id}'
            req = requests.get(url, headers=API_HEADERS)
            json_data = req.json()
            if json_data.get('data'):
                user_info = json_data['data'][0]
                return {'streamer_data': streamer_data, 'user_info': user_info}
    except Exception as e:
        print("Error checking user or getting user info:", e)
    return {}


async def validate_streamer(streamer, append=False):
    """
    This function validates if a streamer is a valid Twitch username.

    Args:
        streamer (str): The username of the streamer to validate.
        append (bool): Whether to append the streamer to the list of streamers to check.

    The function first constructs the URL for the Twitch API endpoint to retrieve user information.
    It then sends a GET request to the Twitch API endpoint with the streamer's username.
    If the response contains any data, the streamer is considered valid.
    If the response does not contain any data, the streamer is considered invalid.

    This function returns a boolean value indicating whether the streamer is valid.
    """
    url = f'{USER_API_URL}?login={streamer}'  # Construct the URL for the Twitch API endpoint.
    try:
        req = requests.get(url, headers=API_HEADERS)  # Send a GET request to the Twitch API endpoint with the API headers.
        json_data = req.json()  # Retrieve the data from the response.
        is_valid = bool(json_data.get('data'))
        if append and is_valid:
            STREAMERS.append(streamer)
            streamers_status[streamer] = False
        return is_valid  # If there is any data, the streamer is valid.
    except Exception as e:
        print("Error validating streamer:", e)


async def notify_discord(datas, bot):
    """
    This function sends a notification to a specific Discord channel when a streamer starts streaming on Twitch.

    Args:
        datas (dict): A dictionary containing the streamer's data and user information.
        bot (discord.Client): The bot instance.

    The function first retrieves the bot channel using the channel_id from the settings. If the bot channel exists,
    it creates an embed message with the streamer's name, game, stream title, profile image, and a link to their
    Twitch stream. The embed message is then sent to the bot channel.

    This function doesn't return anything.
    """
    channel_id = settings.get('twitch_channel_id')  # The ID of the Discord channel to send the notification to.
    bot_channel = bot.get_channel(channel_id)
    if bot_channel:  # If the bot channel exists.
        streamer_data = datas['streamer_data']
        user_info = datas['user_info']
        embed = discord.Embed(
            title=f":tada: {user_info['display_name']} started streaming on Twitch!",
            description=streamer_data['title'],
            color=0x9146ff
        )
        embed.add_field(name="Game", value=streamer_data['game_name'], inline=True)
        embed.add_field(name=":arrow_double_down:", value=f"[Watch here !](https://www.twitch.tv/{user_info['login']})", inline=True)
        embed.set_thumbnail(url=user_info['profile_image_url'])
        embed.set_footer(text="MEE7 Twitch Stream Notifications",
                         icon_url=settings.get('icon_url'))
        await bot_channel.send(embed=embed)
