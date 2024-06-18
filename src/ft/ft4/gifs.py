import random

import discord
import requests
import os

from dotenv import load_dotenv

from src.ft.ft4.keywords import extract_keywords
from src.ft.ft4.sentiments import analyze_sentiment

from src.utilities.settings import Settings

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", ".env"))
load_dotenv(dotenv_path)
settings = Settings()
GIPHY_API_KEY = os.getenv('GIPHY_API_KEY')

GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"


def search_gif(query):
    params = {
        'api_key': GIPHY_API_KEY,
        'q': query,
        'limit': 10
    }
    response = requests.get(GIPHY_SEARCH_URL, params=params)
    data = response.json()
    if data['data']:
        index = random.randint(0, len(data['data']) - 1)
        return data['data'][index]['images']['downsized']['url']
    else:
        return None


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
    keywords = extract_keywords(message.content)  # Extract keywords from the message content.
    # print(f"{sentiment} - {keywords}")
    gif_url = search_gif(f"{keywords}")  # Search for a GIF based on the keywords.
    if gif_url:
        embed = discord.Embed()  # Create a new embed message.
        embed.set_image(url=gif_url)  # Set the image of the embed message to the GIF.
        await message.channel.send(embed=embed)  # Send the embed message to the channel.
    else:
        print(f"No GIF found for keywords: {keywords}.")
