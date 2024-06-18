import random

import requests
import os

from dotenv import load_dotenv

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
