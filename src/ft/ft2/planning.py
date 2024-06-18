import aiohttp
import tempfile
from datetime import datetime, timedelta
import icalendar
import discord

async def download_ical(url: str, file_path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
                print(f'iCal file downloaded to {file_path}')
            else:
                print(f'Failed to download iCal file. Status code: {response.status}')

async def process_ical(file_path: str, ctx):
    """
    This function processes the downloaded iCal file and sends the events of the current week to Discord.

    It reads the iCal file, filters the events for the current week, and sends them as a message.
    """
    with open(file_path, 'rb') as f:
        gcal = icalendar.Calendar.from_ical(f.read())
        current_date = datetime.now().date()
        start_of_week = current_date - timedelta(days=current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        events = []
        for component in gcal.walk():
            if component.name == "VEVENT":
                event_start = component.get('DTSTART').dt
                if isinstance(event_start, datetime):
                    event_start = event_start.date()
                if start_of_week <= event_start <= end_of_week:
                    summary = component.get('SUMMARY')
                    start = component.get('DTSTART').dt
                    end = component.get('DTEND').dt
                    events.append((start, summary, start, end))

        # Sort events by start date
        events.sort()

        if events:
            event_messages = [f"Event: {summary}, Start: {start}, End: {end}" for _, summary, start, end in events]
            for message in split_messages(event_messages):
                await ctx.respond(message)
        else:
            await ctx.respond("No events found for the current week.")

def split_messages(messages, max_length=2000):
    """
    Split a list of messages into chunks that are each less than or equal to max_length characters.
    """
    current_message = ""
    for message in messages:
        if len(current_message) + len(message) + 1 > max_length:
            yield current_message
            current_message = message
        else:
            if current_message:
                current_message += "\n"
            current_message += message
    if current_message:
        yield current_message

