import random

import discord
import requests
import os

from dotenv import load_dotenv
from loguru import logger

from src.ft.ft4.sentiments import analyze_sentiment

from src.utilities.settings import Settings

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", ".env"))
load_dotenv(dotenv_path)
settings = Settings()
TENOR_API_KEY = os.getenv('TENOR_API_KEY')
TENOR_CLIENT_KEY = os.getenv('TENOR_CLIENT_KEY')


def search_gif(query, limit=2):
    """
    This function searches for a GIF using the Tenor API.

    Args:
        query (str): The search term to use when searching for the GIF.
        limit (int, optional): The maximum number of GIFs to return. Defaults to 2.

    Returns: str: The URL of a randomly selected GIF from the search results. If the API request fails, a default GIF URL is returned.

    Raises:
        requests.exceptions.RequestException: If the GET request to the Tenor API fails.
    """
    # Define the parameters for the API request.
    params = {
        'key': TENOR_API_KEY,
        'client_key': TENOR_CLIENT_KEY,
        'q': query,
        'limit': limit
    }

    # Send a GET request to the Tenor API.
    response = requests.get("https://tenor.googleapis.com/v2/search", params=params)

    # If the request was successful, select a random GIF from the results and return its URL.
    if response.status_code == 200 and response.json()['results']:
        return response.json()['results'][random.randint(0, limit - 1)]['media_formats']['gif']['url']
    # If the request was not successful, make a new request with a default query.
    else:
        params.update({'q': 'nothing found', 'limit': 5})
        response = requests.get("https://tenor.googleapis.com/v2/search", params=params)
        if response.status_code == 200 and response.json()['results']:
            return response.json()['results'][random.randint(0, params['limit'] - 1)]['media_formats']['gif']['url']


async def handle_gifs_channel(message):
    """
    This function handles messages sent in the GIFs channel.

    Args:
        message (discord.Message): The message that was sent in the channel.

    The function first analyzes the sentiment of the message content and extracts keywords from it.
    It then searches for a GIF based on the extracted keywords.
    If a GIF URL is found, it creates an embed message with the GIF and sends it to the channel.

    This function doesn't return anything.
    """
    sentiment = analyze_sentiment(message.content)  # Analyze the sentiment of the message content.
    gif_url = search_gif(message.content)  # Search for a GIF based on the keywords.
    if gif_url:
        embed = discord.Embed()  # Create a new embed message.
        embed.set_image(url=gif_url)  # Set the image of the embed message to the GIF.
        await message.channel.send(embed=embed)  # Send the embed message to the channel.
    else:
        logger.error(f"No GIF found for keywords: {message.content}.")
