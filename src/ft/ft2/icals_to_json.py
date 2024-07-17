import json
import os
from loguru import logger


def write_to_json(file_path, data):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

async def register_user_ical(user_id, user_name, file_path, user_icals):
    with open(file_path, 'r') as file:
        content = file.read()
    user_icals[user_id] = content
    user_data = {"user_id": user_id, "ical_content": content}
    write_to_json(f'user_icals/{user_id}.json', user_data)
    logger.debug(f"Registered iCal content for user {user_id}")
