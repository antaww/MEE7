import asyncio
import aiohttp
from datetime import datetime, timedelta, time, date
import icalendar
import pytz
import discord
from collections import defaultdict


async def download_ical(url: str, file_path: str, ctx):
    """
    Asynchronously downloads an iCal file from a given URL and saves it to a specified file path.

    Args:
        url (str): The URL of the iCal file to download.
        file_path (str): The path where the downloaded iCal file should be saved.
        ctx: The Discord context, used to send messages to the Discord channel.

    This function uses the aiohttp library to make an asynchronous HTTP GET request to the URL.
    If the request is successful (HTTP status code 200), it writes the response content to the file at the given path.
    It then sends a message to the Discord context (`ctx`) indicating that the iCal file has been downloaded.
    If the request is not successful, it sends a message to the Discord context indicating that the download failed,
    along with the HTTP status code.
    """
    print("Downloading iCal file from:", url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
                await ctx.respond(f'iCal file downloaded to {file_path}')
            else:
                await ctx.respond(f'Failed to download iCal file. Status code: {response.status}')


def parse_ical(file_path: str, timezone: str = 'Europe/Paris'):
    """
    Parses an iCal file and extracts the events.

    Args:
        file_path (str): The path to the iCal file to parse.
        timezone (str, optional): The timezone to use for the event times. Defaults to 'Europe/Paris'.

    This function reads the iCal file, walks through its components, and extracts the events.
    Each event is a EVENT component with a start time (START), end time (TEND), and summary.
    The start and end times are converted to the specified timezone.
    If the start or end time is a date, it is converted to a datetime at the start of the day in the specified timezone.
    The events are grouped by date and returned as a dictionary mapping dates to lists of events.
    Each event is a tuple containing the summary, start time, and end time.

    Returns:
        dict: A dictionary mapping dates to lists of events.
    """
    with open(file_path, 'rb') as f:
        gcal = icalendar.Calendar.from_ical(f.read())
    events = defaultdict(list)
    for component in gcal.walk():
        if component.name == "VEVENT":
            start = component.get('DTSTART').dt
            end = component.get('DTEND').dt
            summary = component.get('SUMMARY')
            if isinstance(start, datetime):
                start = start.astimezone(pytz.timezone(timezone))
            elif isinstance(start, (datetime, date)):
                start = datetime.combine(start, time.min).replace(tzinfo=pytz.timezone(timezone))
            if isinstance(end, datetime):
                end = end.astimezone(pytz.timezone(timezone))
            elif isinstance(end, (datetime, date)):
                end = datetime.combine(end, time.min).replace(tzinfo=pytz.timezone(timezone))
            events[start.date()].append((summary, start, end))
            print(f"Event found: {start} - {summary}")
    return events


def check_availability(events, start_of_week):
    """
    Checks the availability of a person for a week based on their events.

    Args: events (dict): A dictionary mapping dates to lists of events. Each event is a tuple containing the summary,
    start time, and end time. start_of_week (datetime.date): The date of the start of the week to check availability
    for.

    This function checks the availability of a person for each day of the week starting from the start_of_week. For
    each day, it checks the availability in the morning (08:30 to 12:30), afternoon (13:30 to 17:00), and evening (
    17:00 to 08:30). If there is an event during a time slot, the person is considered not available during that time
    slot. The availability for each day is stored in a dictionary and returned.

    Returns: dict: A dictionary mapping dates to availability. The availability is a dictionary mapping time slots (
    'morning', 'afternoon', 'evening') to a boolean indicating whether the person is available during that time slot.
    """
    week_availability = {}
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        availability = {
            "morning": True,
            "afternoon": True,
            "evening": True
        }

        for summary, start, end in events.get(day, []):
            print(f"Checking event: {summary} from {start} to {end} on {day}")
            # Check morning availability (08:30 to 12:30)
            if (start.time() < datetime.strptime('12:30', '%H:%M').time() and end.time() >
                    datetime.strptime('08:30', '%H:%M').time()):
                availability["morning"] = False
            # Check afternoon availability (13:30 to 17:00)
            if (start.time() < datetime.strptime('17:00', '%H:%M').time() and end.time() >
                    datetime.strptime('13:30', '%H:%M').time()):
                availability["afternoon"] = False
            # Check evening availability (17:00 to 08:30)
            if (start.time() >= datetime.strptime('17:00', '%H:%M').time() or end.time() <=
                    datetime.strptime('08:30', '%H:%M').time()):
                availability["evening"] = False

        print(f"Availability for {day}: {availability}")
        week_availability[day] = availability

    return week_availability


def create_embed_for_week(person, week_availability):
    """
    Creates a Discord embed message for a person's availability for a week.

    Args:
        person (str): The name of the person.
        week_availability (dict): A dictionary mapping dates to availability. The availability is a dictionary mapping time slots ('morning', 'afternoon', 'evening') to a boolean indicating whether the person is available during that time slot.

    This function creates a Discord embed message with the title as the person's name and the color as blue.
    For each day in the week_availability, it adds a field to the embed with the name as the date and the value as the availability for the morning, afternoon, and evening.
    The availability is indicated as 'Available' if the person is available during that time slot, and 'Not Available' otherwise.

    Returns:
        discord.Embed: A Discord embed message for the person's availability for a week.
    """
    embed = discord.Embed(title=f"Availability for {person}", color=discord.Color.blue())
    for day, availability in week_availability.items():
        day_str = day.strftime('%A %d/%m/%Y')
        embed.add_field(name=day_str, value=f"Morning: {'Available' if availability['morning'] else 'Not Available'}\n"
                                            f"Afternoon: {'Available' if availability['afternoon'] else 'Not Available'}\n"
                                            f"Evening: {'Available' if availability['evening'] else 'Not Available'}",
                        inline=False)
    return embed


async def update_embed_with_week(message, file_path, week_offset, person):
    """
    Updates a Discord embed message with a person's availability for a week offset from the current week.

    Args:
        message (discord.Message): The Discord message to edit.
        file_path (str): The path to the iCal file to parse.
        week_offset (int): The number of weeks offset from the current week. Can be negative to indicate past weeks.
        person (str): The name of the person.

    This function calculates the start of the target week based on the current week and the week_offset.
    It then parses the iCal file and checks the availability of the person for the target week.
    It creates a Discord embed message for the person's availability and edits the provided message with the new embed.

    This function is asynchronous and should be awaited.
    """
    current_week_start = datetime.now(pytz.timezone('Europe/Paris')).date() - timedelta(
        days=datetime.now(pytz.timezone('Europe/Paris')).weekday())
    target_week_start = current_week_start + timedelta(weeks=week_offset)
    events = parse_ical(file_path)
    week_availability = check_availability(events, target_week_start)

    embed = create_embed_for_week(person, week_availability)
    await message.edit(embed=embed)


async def is_person_available(file_path: str, person: str, ctx):
    """
    Checks the availability of a person for the current week and sends a Discord message with the results.

    Args:
        file_path (str): The path to the iCal file to parse.
        person (str): The name of the person.
        ctx: The Discord context, used to send messages to the Discord channel.

    This function parses the iCal file and checks the availability of the person for the current week.
    It creates a Discord embed message for the person's availability and sends it to the Discord context (`ctx`).
    It then adds '⬅️' and '➡️' reactions to the scent message.

    This function is asynchronous and should be awaited.
    """
    print(f"Checking availability for person: {person}")
    events = parse_ical(file_path)
    current_week_start = datetime.now(pytz.timezone('Europe/Paris')).date() - timedelta(
        days=datetime.now(pytz.timezone('Europe/Paris')).weekday())
    week_availability = check_availability(events, current_week_start)

    embed = create_embed_for_week(person, week_availability)
    sent_message = await ctx.send(embed=embed)

    await sent_message.add_reaction('⬅️')
    await sent_message.add_reaction('➡️')

    def check(reaction_emoji, user_click):
        """
        Checks if the reaction added to the message is from the author and is either '⬅️' or '➡️'.

        Args:
            reaction_emoji: The reaction added to the message.
            user_click: The user who added the reaction.

        Returns:
            bool: True if the reaction is from the author and is either '⬅️' or '➡️', False otherwise.
        """
        return user_click == ctx.author and str(reaction_emoji.emoji) in ['⬅️', '➡️']

    current_week_offset = 0
    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == '⬅️':
                current_week_offset -= 1
            elif str(reaction.emoji) == '➡️':
                current_week_offset += 1

            await update_embed_with_week(sent_message, file_path, current_week_offset, person)
            await sent_message.remove_reaction(reaction.emoji, user)
        except asyncio.TimeoutError:
            break


async def register_user_ical(user_id, file_path, user_icals):
    """
    Registers a user's iCal file.

    Args:
        user_id: The ID of the user.
        file_path (str): The path to the iCal file.
        user_icals (dict): A dictionary mapping user IDs to iCal file paths.

    This function adds the user's iCal file path to the user_icals dictionary with the user ID as the key.
    It then prints a message indicating that the iCal file has been registered for the user.
    """
    user_icals[user_id] = file_path
    print(f"Registered iCal file for user {user_id}")


async def is_everyone_available(ctx, user_icals):
    """
    Checks the availability of all users for the current week and sends a Discord message with the results.

    Args:
        ctx: The Discord context, used to send messages to the Discord channel.
        user_icals (dict): A dictionary mapping user IDs to iCal file paths.

    This function iterates over the user_icals dictionary and checks the availability of each user for the current week.
    The availability of each user is stored in a dictionary and sent to the Discord context (`ctx`).

    This function is asynchronous and should be awaited.
    """
    print("Checking availability for all users")
    all_availabilities = {}
    for user_id, file_path in user_icals.items():
        print(f"Checking availability for user: {user_id}")
        availability = await is_person_available(file_path, user_id, ctx)
        all_availabilities[user_id] = availability

    for user_id, availability in all_availabilities.items():
        await ctx.respond(f"User {user_id} availability: {availability}")


def split_messages(messages, max_length=2000):
    """
    Splits a list of messages into chunks, each with a maximum length.

    Args:
        messages (list): A list of messages to split. Each message is a string.
        max_length (int, optional): The maximum length of each chunk. Defaults to 2000.

    This function iterates over the list of messages and adds each message to the current chunk.
    If adding a message to the current chunk would exceed the max_length, it yields the current chunk and starts a new one.
    After all messages have been processed, it yields the last chunk if it is not empty.

    Yields:
        str: A chunk of messages. The length of each chunk is less than or equal to max_length.
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
