import asyncio
import json
import os
from datetime import datetime, timedelta, time, date
from collections import defaultdict

import aiohttp
import icalendar
import pytz
import discord

TEMP_DIR = 'temp_icals'
EVENTS = []


def ensure_temp_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


async def download_ical(url: str, file_path: str, ctx):
    """
    Asynchronously downloads an iCal file from a specified URL and saves it to a given file path.

    This function attempts to download an iCal (.ics) file from the provided URL. If the download is successful,
    the file is saved to the specified path on the local file system. If the download fails (e.g., due to a network error
    or the server responding with a status code other than 200), an error message is sent to the provided context (ctx),
    typically a Discord context in this application, indicating the failure.

    Args:
        url (str): The URL from which to download the iCal file.
        file_path (str): The local file system path where the downloaded file should be saved.
        ctx: The context in which this function is called, used here to send messages back to a Discord channel.

    Returns:
        None. The function's primary side effects are saving a file to the disk or sending a message through Discord.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
            else:
                await ctx.send(f'Failed to download iCal file. Status code: {response.status}')


def parse_ical_content(ical_content: str, timezone: str = 'Europe/Paris'):
    """
    Parses the content of an iCal file and organizes events by date.

    This function takes the content of an iCal file as a string and a timezone string. It processes the iCal content
    to extract events (VEVENT components) and organizes them by their start date. Each event's start and end times
    are adjusted to the specified timezone. The function returns a dictionary where keys are dates and values are lists
    of tuples, each tuple containing the event summary, start datetime, and end datetime, all adjusted to the specified timezone.

    Args:
        ical_content (str): The content of an iCal file as a string.
        timezone (str): The timezone to which the event times will be converted. Defaults to 'Europe/Paris'.

    Returns:
        dict: A dictionary where each key is a date (datetime.date object) and each value is a list of tuples.
              Each tuple contains three elements: the event summary (str), the start datetime (datetime.datetime),
              and the end datetime (datetime.datetime), all adjusted to the specified timezone.
    """
    gcal = icalendar.Calendar.from_ical(ical_content)
    events = defaultdict(list)
    for component in gcal.walk():
        if component.name == "VEVENT":
            start = component.get('DTSTART').dt
            end = component.get('DTEND').dt
            summary = component.get('SUMMARY')

            if summary:
                city_part = summary.split("|")[0]
                city = city_part.split(" - ")[-1].strip()
                EVENTS.append(city)
            else:
                print("Warning: SUMMARY not found in event")

            if isinstance(start, datetime):
                start = start.astimezone(pytz.timezone(timezone))
            elif isinstance(start, (datetime, date)):
                start = datetime.combine(start, time.min).replace(tzinfo=pytz.timezone(timezone))
            if isinstance(end, datetime):
                end = end.astimezone(pytz.timezone(timezone))
            elif isinstance(end, (datetime, date)):
                end = datetime.combine(end, time.min).replace(tzinfo=pytz.timezone(timezone))
            events[start.date()].append((summary, start, end))

    if not os.path.exists('events_locations'):
        os.makedirs('events_locations')
    with open('events_locations/events_locations.json', 'w') as f:
        json.dump(EVENTS, f)
    return events


def check_availability(events, start_of_week):
    """
    Determines the daily availability of a person based on their scheduled events for a week.

    This function iterates through each day of a week starting from a given date. For each day, it checks the scheduled
    events and updates the availability for morning, afternoon, and evening based on the event times. The availability
    for each period is set to False if there is any event overlapping with the predefined time slots for morning
    (08:30 to 12:30), afternoon (13:30 to 17:00), and evening (after 17:00 or before 08:30 the next day).

    Args:
        events (dict): A dictionary where keys are dates (datetime.date objects) and values are lists of tuples.
                       Each tuple contains the event summary (str), the start datetime (datetime.datetime),
                       and the end datetime (datetime.datetime) of an event.
        start_of_week (datetime.date): The date representing the first day of the week for which to check availability.

    Returns:
        dict: A dictionary where keys are dates (datetime.date objects) and values are dictionaries. Each value dictionary
              has keys 'morning', 'afternoon', and 'evening' with boolean values indicating availability for those periods.
    """
    week_availability = {}
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        availability = {"morning": True, "afternoon": True, "evening": True}
        for summary, start, end in events.get(day, []):
            if (start.time() < datetime.strptime('12:30', '%H:%M').time() and end.time() > datetime.strptime('08:30',
                                                                                                             '%H:%M').time()):
                availability["morning"] = False
            if (start.time() < datetime.strptime('17:00', '%H:%M').time() and end.time() > datetime.strptime('13:30',
                                                                                                             '%H:%M').time()):
                availability["afternoon"] = False
            if (start.time() >= datetime.strptime('17:00', '%H:%M').time() or end.time() <= datetime.strptime('08:30',
                                                                                                              '%H:%M').time()):
                availability["evening"] = False
        week_availability[day] = availability
    return week_availability


def create_embed_for_week(person, week_availability):
    """
    Creates a Discord embed message displaying a person's availability for each day of a week.

    This function iterates over each day in the `week_availability` dictionary, formatting the availability
    information into a Discord embed. The embed displays the person's name in the title and lists each day of the week
    with the person's availability for morning, afternoon, and evening. Availability is marked with a check mark
    for available times and an 'x' for unavailable times.

    Args:
        person (str): The name of the person whose availability is being checked.
        week_availability (dict): A dictionary where keys are `datetime.date` objects representing each day of the week,
                                  and values are dictionaries with keys 'morning', 'afternoon', and 'evening'. Each key
                                  maps to a boolean indicating availability for that time period.

    Returns:
        discord.Embed: An embed object ready to be sent in a Discord message, containing the availability information.
    """
    embed = discord.Embed(title=f"Availability for {person}", color=discord.Color.blue())
    for day, availability in week_availability.items():
        day_str = day.strftime('%A %d/%m/%Y')
        embed.add_field(
            name=day_str,
            value=(
                f"Morning: {'Available :white_check_mark:' if availability['morning'] else 'Not Available :x:'}\n"
                f"Afternoon: {'Available :white_check_mark:' if availability['afternoon'] else 'Not Available :x:'}\n"
                f"Evening: {'Available :white_check_mark:' if availability['evening'] else 'Not Available :x:'}"
            ),
            inline=False,
        )
    return embed


async def update_embed_with_week(message, ical_content, week_offset, person):
    """
    Updates a Discord message with an embed representing a person's availability for a specific week.

    This asynchronous function calculates the start date of a target week based on the current date and a specified
    offset in weeks. It then parses the iCal content to determine the person's availability for that week and updates
    the provided Discord message with a new embed reflecting this availability.

    Args:
        message (discord.Message): The Discord message to be updated with the new embed.
        ical_content (str): The content of an iCal file as a string, containing the events to be considered for
                            calculating availability.
        week_offset (int): The number of weeks to offset from the current week to find the target week. Can be
                           positive (future weeks), zero (current week), or negative (past weeks).
        person (str): The name of the person whose availability is being checked.

    Returns:
        None. The function's primary side effect is updating a Discord message with a new embed.
    """
    current_week_start = datetime.now(pytz.timezone('Europe/Paris')).date() - timedelta(
        days=datetime.now(pytz.timezone('Europe/Paris')).weekday())
    target_week_start = current_week_start + timedelta(weeks=week_offset)
    events = parse_ical_content(ical_content)
    week_availability = check_availability(events, target_week_start)
    embed = create_embed_for_week(person, week_availability)
    await message.edit(embed=embed)

async def is_everyone_available(ctx, json_file_path: str):
    """
    Asynchronously checks and displays the availability of all users for the current week in a Discord channel.

    This function reads user data from a specified JSON file, including user IDs and their corresponding iCal content.
    It then calculates each user's availability for the current week based on their iCal events. For each user, it creates
    a Discord embed message displaying their availability and collects these embeds in a list to be potentially sent or
    processed further.

    The function is designed to handle multiple users' availabilities but currently processes only one user's data from
    the JSON file. Future enhancements could iterate over multiple users within the JSON file.

    Args:
        ctx: The context in which this function is called, used here to potentially send messages back to a Discord channel.
        json_file_path (str): The file system path to the JSON file containing user data (user IDs and iCal content).

    Returns:
        list: A list of discord.Embed objects, each representing the availability of a user for the current week.
    """
    with open(json_file_path, 'r') as json_file:
        user_data = json.load(json_file)

    user_id = user_data["user_id"]
    ical_content = user_data["ical_content"]

    embeds = []
    events = parse_ical_content(ical_content)
    current_week_start = datetime.now(pytz.timezone('Europe/Paris')).date() - timedelta(
        days=datetime.now(pytz.timezone('Europe/Paris')).weekday())
    week_availability = check_availability(events, current_week_start)
    embed = create_embed_for_week(user_id, week_availability)
    embeds.append(embed)

    return embeds