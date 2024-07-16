import json
import os
import tempfile
from datetime import datetime, timedelta
import aiohttp
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import pytz
from collections import defaultdict

def write_to_json(file_path, data):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def read_from_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    return {}

async def register_user_ical(user_id, user_name, file_path, user_icals):
    with open(file_path, 'r') as file:
        content = file.read()
    user_icals[user_id] = content
    # Write to JSON
    user_data = {"user_id": user_id, "ical_content": content}
    write_to_json(f'user_icals/{user_name}.json', user_data)
    print(f"Registered iCal content for user {user_id}")

def load_user_icals():
    if not os.path.exists('user_icals'):
        os.makedirs('user_icals')
    for filename in os.listdir('user_icals'):
        if filename.endswith('.json'):
            data = read_from_json(f'user_icals/{filename}')
            user_id = data.get('user_id')
            content = data.get('ical_content')
            user_icals[user_id] = content

user_icals = {}
load_user_icals()
