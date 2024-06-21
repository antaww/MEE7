# scrap https://squad.royaleapi.com/abilities/ultras.html
import json

import requests
from bs4 import BeautifulSoup

from abilities import generate_ultras

api = "https://squad.royaleapi.com"
ultras = "/abilities/ultras.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
response = requests.get(api + ultras, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

generate_ultras(soup, api)
