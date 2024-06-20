import os
import requests


async def get_events(topic, location):
    url = f"https://www.eventbriteapi.com/v3/events/search/?q={topic}&location.address={location}"
    headers = {
        "Authorization" : f"Bearer {os.getenv('EVENTBRITE_API_KEY')}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json().get("events", [])
        return events
    return []

