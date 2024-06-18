import aiohttp
import tempfile
from datetime import datetime, timedelta
import icalendar
import pytz
import discord
from collections import defaultdict


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
        current_date = datetime.now(pytz.timezone('Europe/Paris')).date()
        start_of_week = current_date - timedelta(days=current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        events = defaultdict(list)
        for component in gcal.walk():
            if component.name == "VEVENT":
                event_start = component.get('DTSTART').dt
                if isinstance(event_start, datetime):
                    event_start = event_start.astimezone(pytz.timezone('Europe/Paris')).date()
                if start_of_week <= event_start <= end_of_week:
                    summary = component.get('SUMMARY')
                    summary = summary.split('|')[0].strip()  # Stop at first | and strip any leading/trailing spaces
                    start = component.get('DTSTART').dt
                    end = component.get('DTEND').dt
                    start = start.astimezone(pytz.timezone('Europe/Paris'))
                    end = end.astimezone(pytz.timezone('Europe/Paris'))
                    start_formatted = start.strftime('%d/%m/%Y %H:%M')
                    end_formatted = end.strftime('%d/%m/%Y %H:%M')
                    events[event_start].append((summary, start_formatted, end_formatted))

        # Sort events by start date
        for date in events:
            events[date].sort(key=lambda event: datetime.strptime(event[1], '%d/%m/%Y %H:%M'))

        if events:
            event_messages = []
            for date, day_events in sorted(events.items()):
                event_messages.append(f"Date: {date.strftime('%d/%m/%Y')}")
                for summary, start, end in day_events:
                    event_messages.append(f"    Event: {summary}, Start: {start}, End: {end}")
                event_messages.append("")  # Add an empty line for better readability

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
