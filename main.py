import json
import os
from datetime import datetime, timezone, timedelta
import re
from datetime import datetime
import locale
import pytz
from loguru import logger

import discord
from discord import Option
from discord.ext import tasks, commands
from dotenv import load_dotenv
from discord.ui import Select, View
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from src.ft.bonus.squadbusters.navigation import NavigationView
from src.ft.ft1.recommendations import generate_recommendations
from src.ft.ft1.stream_notifications import check_streamers, validate_streamer
from src.ft.ft2.icals_to_json import register_user_ical
from src.ft.ft2.planning import is_everyone_available, download_ical, ensure_temp_dir, TEMP_DIR, parse_ical_content, \
    check_availability
from src.ft.ft2.weather import get_weather
from src.ft.ft3.profanities import handle_profanities
from src.ft.ft3.warnings import Warnings
from src.ft.ft4.gifs import handle_gifs_channel
from src.ft.ft5.gpt import GPT
from src.ft.ft5.reports import Reports
from src.utilities.settings import Settings
from src.utilities.utilities import setup_commands, get_current_date_formatted

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Bot(intents=intents)
settings = Settings()
warnings = Warnings()
reports = Reports()

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

def load_user_icals(directory='user_icals'):
    user_icals = {}
    if not os.path.exists(directory):
        os.makedirs(directory)
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            user_id = filename.split('.')[0]
            user_icals[user_id] = os.path.join(directory, filename)
    return user_icals


user_icals = load_user_icals()


@bot.event
async def on_ready():
    """
    This function is an event handler that gets triggered when the bot is ready.
    This function doesn't take any arguments and doesn't return anything.
    """
    logger.success(f'Bot is ready. Logged in as {bot.user}')
    await handle_tasks()


async def handle_tasks():
    scheduled_recommendation.start()
    check_streamers.start(bot)
    scheduled_update.start()
    scheduled_reports_save.start()
    #scheduled_report.start()
    scheduled_activity_recommendation.start()


@tasks.loop(hours=24)
async def scheduled_update():
    """
    This function is a task that runs every 24 hours.

    The function executes the "scraper.py" script located in the "src/ft/bonus/squadbusters" directory.
    The purpose of this script is to update the data used by the bot.

    This function doesn't take any arguments and doesn't return anything.
    """
    logger.info("Updating squadbusters data...")
    os.system("python src/ft/bonus/squadbusters/scraper.py")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild.id != 1252165373256794185:
        logger.debug(f"Message from {message.guild.name}")
        return

    await handle_profanities(message)

    if message.channel.id == settings.get('gifs_channel_id'):
        await handle_gifs_channel(message)

    # reports
    if message.channel.id == settings.get('recommended_channel_id'):
        if not reports.is_spam(message):
            reports.add_message(message)


@tasks.loop(minutes=1)
async def scheduled_reports_save():
    logger.info("Saving reports data...")
    reports.save_messages()


# minimum timing : 2 minutes (free plan limitation : 30 messages per hour)
@tasks.loop(minutes=6)  # todo: change to hours=24 (for testing purposes, we set it to minutes=3)
async def scheduled_report():
    # Do not run the task right after the bot starts, execute it 1 / 2 timing
    if scheduled_report.current_loop == 0:
        return
    global gpt
    try:
        gpt = GPT()
        gpt.login()
        prompt = gpt.generate_report_prompt()
        response = gpt.send_prompt(prompt) if prompt else ""
        logger.debug(f"ChatGPT response: {response}")
        if response:
            messages = re.findall(r'\[Message \d+\] "(.*?)"', response)
            sentiment_match = re.search(r'Global sentiment: (.*)"', response)
            sentiment = sentiment_match.group(1) if sentiment_match else "No sentiment found"
        else:
            messages = []
            sentiment = "No sentiment found"
        # send the response to moments_channel_id
        moments_channel_id = settings.get('moments_channel_id')
        moments_channel = bot.get_channel(moments_channel_id)
        unique_authors = reports.get_unique_authors()
        all_warnings = warnings.get_all_daily_warnings()
        warnings_description = "\n> ".join([f"- **{i + 1}**. {bot.get_user(int(user_id)).mention} - {count} warning(s)"
                                            for i, (user_id, count) in enumerate(all_warnings.items())]) \
            if all_warnings else "- No warnings found."

        if moments_channel:
            message = await moments_channel.send(
                f"> # :crystal_ball: **Daily discussion report**\n"
                f"> ## {get_current_date_formatted(separator="/")}\n"
                f"> **Sentiment** : \n> - {sentiment}\n"
                f"> **Impactful messages** : \n> - {'\n> - '.join(messages) or 'No impactful messages found'}"
                f"\n> **Participants** : \n> - {', '.join([f'<@{author}>' for author in unique_authors]) or 
                                                'No participants found'}"
                f"\n> **Warnings** : \n> {warnings_description}"
            )
            # generate word cloud for messages
            if messages:
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(messages))
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.savefig('wordcloud.png')
                plt.close()
                await message.reply(file=discord.File('wordcloud.png'))
                os.remove('wordcloud.png')

            # generate tree map for warnings
            if all_warnings:
                labels = [bot.get_user(int(user_id)).name for user_id in all_warnings.keys()]
                sizes = [count for count in all_warnings.values()]
                colors = np.random.rand(len(labels), 3)
                plt.figure(figsize=(10, 5))
                plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
                plt.axis('equal')
                plt.title('Warnings Distribution')
                plt.savefig('warnings.png')
                plt.close()
                await message.reply(file=discord.File('warnings.png'))
                os.remove('warnings.png')
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        try:
            gpt.close()
        except OSError:
            pass


# scheduled_activity_recommendation & scheduled_report must be at least 3 minutes apart
@tasks.loop(minutes=3)
async def scheduled_activity_recommendation():
    global gpt
    try:
        city = "Aix-en-provence"  # todo: call get_location_from_ical
        date = "2024-07-17"  # todo: call get_date_from_ical
        weather_datas = get_weather(city, date)
        gpt = GPT()
        gpt.login()
        prompt = gpt.generate_activity_prompt(weather_datas)
        response = gpt.send_prompt(prompt) if prompt else ""
        logger.debug(f"ChatGPT response: {response}")
        if response:
            activities_names = re.findall(r'Activity \d+: (.*?) :', response)
            urls = re.findall(r'Activity \d+: .*? : (https?://\S+)', response)
            print(activities_names)
            print(urls)
        else:
            activities = []
            urls = []
        # send the response to moments_channel_id
        activity_channel_id = settings.get('activity_channel_id')
        activity_channel = bot.get_channel(activity_channel_id)
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%Y')
        if activity_channel:
            await activity_channel.send(
                f"> # :tada: **Activity recommendation at {city}**\n"
                f"> ## {formatted_date}\n"
                f"> :white_sun_rain_cloud: **Weather** : {weather_datas['weather']}\n"
                f"> :thermometer: **Temperature** : {weather_datas['temperature']}°C\n"
                f"> :hourglass_flowing_sand: **Activities** : \n> - {'\n> - '.join([f'{activity_name} : [Read more]({url})' for activity_name, url in zip(activities_names, urls)]) or 'No activities found'}"
            )
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        try:
            gpt.close()
        except OSError:
            pass

@tasks.loop(hours=1)
async def scheduled_recommendation():
    """
    This function is a task that runs every hour. Its purpose is to send a recommendation message to a specific channel.

    The function first retrieves the channel using the channel_id. If the channel exists, it sends a message
    indicating that it's analyzing and recommending content. It then calls the `analyze_and_recommend` function with
    the bot and channel_id as arguments to get the recommendation. The recommendation is then sent to the channel.

    This function doesn't take any arguments and doesn't return anything.
    """
    recommended_channel_id = settings.get('recommended_channel_id')
    recommended_channel = bot.get_channel(recommended_channel_id)
    channel_id = settings.get('recommendations_channel_id')
    channel = bot.get_channel(channel_id)

    if channel and recommended_channel:
        message = await channel.send(
            f"> # :alarm_clock: **Scheduled recommendation**\n"
            f"> Analyzing and recommending content in {recommended_channel.name}..."
        )
        recommendation = await generate_recommendations(bot, recommended_channel, recommended_channel_id)

        await message.reply(recommendation)


@bot.command(name="recommend", description="Recommends content based on recent discussions")
async def recommend(ctx, channel: discord.TextChannel):
    """
    This function is a command handler for the 'recommend' command.

    It takes two arguments: - ctx: The context in which the command was called. This includes information about the
    message, the channel, and the user who called the command. - channel_id: The ID of the channel for which to
    recommend content. This should be a string.

    The function first checks if the channel_id is a digit. If it is, it converts it to an integer and checks if a
    channel with that ID exists. If the channel exists, it calls the `analyze_and_recommend` function with the bot
    and channel_id as arguments to get the recommendation. The recommendation is then sent as a response to the
    command. If the channel doesn't exist, it sends a response indicating that the channel was not found for
    analysis. If the channel_id is not a digit, it sends a response indicating that the channel ID is invalid.

    This function doesn't return anything.
    """
    channel_id = channel.id
    channel = bot.get_channel(channel_id)
    if channel:
        recommendation = await generate_recommendations(bot, channel, channel_id)
        await ctx.respond(recommendation)
    else:
        await ctx.respond("Channel not found for analysis.")


@bot.command(name="warnings", description="Displays the warnings for a user or all users")
async def display_warnings(ctx, user: discord.User = None):
    """
    This function is a command handler for the 'warnings' command.

    Args: ctx (discord.Context): The context in which the command was called. user (discord.User, optional): The user
    for whom to display warnings. If not provided, warnings for all users are displayed.

    The function first checks if a user was provided. If a user was provided, it retrieves the warnings for that user
    and sends a response with the number of warnings. If no user provided, it retrieves the warnings for all
    users. If there are any warnings, it creates a description string with the warnings for each user and sends a
    response with an embed message containing the warnings. If there are no warnings, it sends a response indicating
    that no warnings were found.

    This function doesn't return anything.
    """
    if user:
        await ctx.respond(f"{user.mention} has {warnings.get_user_warnings(user.id)} warning(s).")
    else:
        all_warnings = warnings.get_all_warnings()
        if all_warnings:
            description = "\n".join([f"**{i + 1}**. {ctx.guild.get_member(int(user_id)).mention} - {count} warning(s)"
                                     for i, (user_id, count) in enumerate(all_warnings.items())])
        else:
            description = "No warnings found."
        embed = discord.Embed(title=f":warning: Warnings Summary of {ctx.guild.name}",
                              color=discord.Color.red(),
                              description=description)
        embed.set_footer(text="MEE7 Warning System",
                         icon_url=settings.get('icon_url'))
        await ctx.respond(embed=embed)


@bot.command(name="register_ical", description="Register your iCal file for availability checks")
async def register_ical(ctx, url: discord.Option(discord.SlashCommandOptionType.string)):
    ensure_temp_dir()
    temp_file_path = os.path.join(TEMP_DIR, 'temp.ics')
    await download_ical(url, temp_file_path, ctx)
    await register_user_ical(ctx.author.id, ctx.author.name, temp_file_path, user_icals)
    await planning(ctx)
    await ctx.respond(f":white_check_mark: Your iCal file has been registered successfully.")


@bot.command(name="disponibilites", description="Displays the availabilities of all persons in the Discord server")
async def disponibilites(ctx):
    users = ctx.guild.members
    users = [user for user in users if not user.bot]

    if not users:
        await ctx.respond("No users found in the Discord server.")
        return

    options = [discord.SelectOption(label=member.display_name, value=str(member.id)) for member in users]

    select = Select(placeholder="Choose a user", options=options)
    async def select_callback(interaction):
        user_id = int(select.values[0])
        async with ctx.typing():
            embeds = await is_everyone_available(ctx, f"user_icals/{user_id}.json")
            for embed in embeds:
                await ctx.respond(embed=embed)

    select.callback = select_callback
    view = View()
    view.add_item(select)

    await ctx.respond("Select a user to view their availability:", view=view)


def aggregate_weekly_events(directory='user_icals'):
    aggregated_events = {}
    current_week_start = get_current_week_start()

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as json_file:
                user_data = json.load(json_file)
                user_id = str(user_data["user_id"])
                ical_content = user_data.get("ical_content", "")

                if ical_content:
                    events = parse_ical_content(ical_content)
                    if events is None:
                        continue
                    week_events = check_availability(events, current_week_start)

                    # Convert date keys to string keys
                    week_events_str_keys = {day.isoformat(): availability for day, availability in week_events.items()}

                    aggregated_events[user_id] = week_events_str_keys

    return aggregated_events
async def planning(ctx):
    ensure_temp_dir()
    users = ctx.guild.members
    users = [user for user in users if not user.bot]

    if not users:
        await ctx.respond("No users found in the Discord server.")
        return

    aggregated_events = aggregate_weekly_events()

    if not aggregated_events:
        await ctx.respond("No events found for the current week.")
        return

    combined_json = json.dumps(aggregated_events, indent=4)

    # Send the JSON as a file
    with open("aggregated_events.json", "w") as json_file:
        json_file.write(combined_json)

@bot.command(name="display_common_availability", description="Displays common availability of all users for the current week")
async def display_common_availability(ctx):
    weekly_events = aggregate_weekly_events()
    all_users = ctx.guild.members

    time_slots = ["morning", "afternoon", "evening"]

    common_availability = {}

    for user in all_users:
        user_id = str(user.id)
        if user_id in weekly_events:
            user_name = user.display_name
            for day, times in weekly_events[user_id].items():
                if day not in common_availability:
                    common_availability[day] = {slot: [] for slot in time_slots}
                for time_slot in time_slots:
                    if times.get(time_slot) is True:
                        common_availability[day][time_slot].append(user_name)

    max_availability = {slot: 0 for slot in time_slots}
    for slots in common_availability.values():
        for time_slot, users in slots.items():
            max_availability[time_slot] = max(max_availability[time_slot], len(users))

    embed = discord.Embed(title="Common Availability for All Users", color=discord.Color.green())

    for day, slots in common_availability.items():

        date_obj = datetime.strptime(day, '%Y-%m-%d')
        french_day = date_obj.strftime('%A %d %B')
        french_day = french_day.capitalize()

        morning_users = ", ".join(slots["morning"])
        afternoon_users = ", ".join(slots["afternoon"])
        evening_users = ", ".join(slots["evening"])

        day_star = ""
        if all(len(slots[slot]) > 0 for slot in time_slots):
            day_star = "⭐"

        availability_str = (
            f"```\nMatin: {morning_users}\n"
            f"Après-midi: {afternoon_users}\n"
            f"Soir: {evening_users}\n```"
        )
        embed.add_field(name=f"{french_day} {day_star}", value=availability_str, inline=False)

    await ctx.respond(embed=embed)

def get_current_week_start():
    return datetime.now(pytz.timezone('Europe/Paris')).date() - timedelta(
        days=datetime.now(pytz.timezone('Europe/Paris')).weekday())

@bot.command(name="add_streamer", description="Adds a streamer to the list of streamers to check")
@commands.has_permissions(administrator=True)
async def add_streamer(ctx, streamer: discord.Option(discord.SlashCommandOptionType.string)):
    """
    This function is a command handler for the 'add_streamer' command.

    It takes two arguments:
    - ctx: The context in which the command was called.
    - streamer: The name of the streamer to add to the list of streamers to check.

    The function first validates the streamer name using the `validate_streamer` function. If the streamer is valid,
    it adds the streamer to the list of streamers to check and sends a success message. If the streamer is invalid,
    it sends an error message.
    """
    streamer = streamer.lower().replace(" ", "")
    if await validate_streamer(streamer, append=True):
        settings.add_streamer(streamer)
        await ctx.respond(f":white_check_mark: {streamer} has been added to the list of streamers to check.")
    else:
        await ctx.respond(f":x: {streamer} is not a valid Twitch username.")


@bot.command(name="top10messages", description="Displays the top 10 users who sent the most messages today.")
async def top10messages(ctx, bots: discord.Option(discord.SlashCommandOptionType.boolean) = False):
    await ctx.respond("Calculating, this may take a moment...")

    message_counts = {}
    today = datetime.now(timezone.utc).date()

    # Iterate through all channels in the server
    for channel in ctx.guild.text_channels:
        async for message in channel.history(limit=None,
                                             after=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)):
            if message.author.bot and not bots:
                continue
            if message.author.id in message_counts:
                message_counts[message.author.id] += 1
            else:
                message_counts[message.author.id] = 1

    # Sort users by message count
    sorted_counts = sorted(message_counts.items(), key=lambda item: item[1], reverse=True)
    top10 = sorted_counts[:10]

    if not top10:
        # No messages found today
        embed = discord.Embed(title=f"No messages found today ({today})",
                              description="No data available for top 10 users by message count.",
                              color=discord.Color.blue())
        embed.set_footer(text="MEE7 Stats", icon_url=settings.get('icon_url'))
        await ctx.respond(embed=embed)
        return

    # Extract usernames and message counts
    user_names = []
    message_numbers = []
    for user_id, count in top10:
        user = await bot.fetch_user(user_id)
        user_names.append(f"{user.name}#{user.discriminator}" if user.discriminator != "0" else user.name)
        message_numbers.append(count)

    # Generate the graph
    plt.figure(figsize=(10, 5))
    plt.bar(user_names, message_numbers, color='skyblue')
    for i, v in enumerate(message_numbers):
        plt.text(i, v + 0.5, str(v), ha='center', va='bottom')
    plt.xlabel('Users')
    plt.ylabel('Message Count')
    plt.title(f"Top 10 Users by Message Count (Today, {today})")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the graph to a file
    plt.savefig('top10messages.png')
    plt.close()

    # Send the graph on Discord in an embed
    embed = discord.Embed(title=f"Top 10 Users by Message Count (Today, {today})",
                          color=discord.Color.blue())
    embed.set_image(url="attachment://top10messages.png")
    embed.set_footer(text="MEE7 Stats", icon_url=settings.get('icon_url'))
    await ctx.respond(embed=embed, file=discord.File('top10messages.png'))
    os.remove('top10messages.png')


@bot.command(name='sb-ultras', description='Display the list of ultra abilities')
async def sb_ultras(ctx, character: Option(str, "The character name (Archer Queen, Barbarian...)", required=False)):
    with open("src/ft/bonus/squadbusters/abilities.json", "r") as file:
        abilities_data = json.load(file)
    characters = [character for character in abilities_data.keys() if character != 'description']

    if character:
        character = character.lower().replace(" ", "-")
        if character in abilities_data:
            start_index = characters.index(character)
        else:
            await ctx.respond(f"Character **{character}** not found.")
            return
    else:
        start_index = 0

    view = NavigationView(characters, abilities_data, start_index)
    embed = view.update_embed()
    await ctx.respond(embed=embed, view=view)


setup_commands(bot)
bot.run(DISCORD_BOT_TOKEN)
