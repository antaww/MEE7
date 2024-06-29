import json
import os
import tempfile
from datetime import datetime, timezone
from datetime import timedelta

import discord
import matplotlib.pyplot as plt
import pytz
from discord import Option
from discord.ext import tasks, commands
from dotenv import load_dotenv

from src.ft.bonus.squadbusters.navigation import NavigationView
from src.ft.ft1.recommandations import analyze_and_recommend
from src.ft.ft1.stream_notifications import check_streamers, validate_streamer
from src.ft.ft2.planning import download_ical, is_person_available, is_everyone_available, register_user_ical, \
    parse_ical, check_availability, create_embed_for_week
from src.ft.ft3.profanities import handle_profanities
from src.ft.ft3.warnings import Warnings
from src.ft.ft4.gifs import handle_gifs_channel
from src.utilities.settings import Settings
from src.utilities.utilities import setup_commands

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Bot(intents=intents)
settings = Settings()
warnings = Warnings()

# Dictionnaire pour stocker les fichiers iCal par utilisateur
user_icals = {}


@bot.event
async def on_ready():
    """
    This function is an event handler that gets triggered when the bot is ready.
    This function doesn't take any arguments and doesn't return anything.
    """
    print(f'Bot is ready. Logged in as {bot.user}')
    await handle_tasks()


async def handle_tasks():
    scheduled_recommendation.start()
    check_streamers.start(bot)
    scheduled_update.start()


@tasks.loop(hours=24)
async def scheduled_update():
    """
    This function is a task that runs every 24 hours.

    The function executes the "scraper.py" script located in the "src/ft/bonus/squadbusters" directory.
    The purpose of this script is to update the data used by the bot.

    This function doesn't take any arguments and doesn't return anything.
    """
    print("Updating squadbusters data...")
    os.system("python src/ft/bonus/squadbusters/scraper.py")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild.id != 1252165373256794185:
        print(f"Message from {message.guild.name}")
        return

    await handle_profanities(message)

    if message.channel.id == settings.get('gifs_channel_id'):
        await handle_gifs_channel(message)


@tasks.loop(hours=1)
async def scheduled_recommendation():
    """
    This function is a task that runs every hour. Its purpose is to send a recommendation message to a specific channel.

    The function first retrieves the channel using the channel_id. If the channel exists, it sends a message
    indicating that it's analyzing and recommending content. It then calls the `analyze_and_recommend` function with
    the bot and channel_id as arguments to get the recommendation. The recommendation is then sent to the channel.

    This function doesn't take any arguments and doesn't return anything.
    """
    channel_id = settings.get('recommendations_channel_id')
    channel = bot.get_channel(channel_id)

    if channel:
        message = await channel.send(
            f"> # :alarm_clock: **Scheduled recommendation**\n> Analyzing and recommending content in {channel.name}..."
        )
        recommendation = await analyze_and_recommend(bot, channel_id)
        await message.reply(recommendation)


@bot.command(name="recommend", description="Recommends content based on recent discussions")
async def recommend(ctx, channel_id: discord.Option(discord.SlashCommandOptionType.string)):
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
    if channel_id.isdigit():
        channel_id = int(channel_id)
        if bot.get_channel(channel_id):
            recommendation = await analyze_and_recommend(bot, channel_id)
            await ctx.respond(recommendation)
        else:
            await ctx.respond("Channel not found for analysis.")
    else:
        await ctx.respond("Invalid channel ID.")


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


@bot.command(name="planning", description="Displays the events of the current week")
async def planning(ctx, url: discord.Option(discord.SlashCommandOptionType.string)):
    print("Command 'planning' called")
    async with ctx.typing():
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ics') as temp_file:
            await download_ical(url, temp_file.name, ctx)
            events = parse_ical(temp_file.name)
            current_week_start = datetime.now(pytz.timezone('Europe/Paris')).date() - timedelta(
                days=datetime.now(pytz.timezone('Europe/Paris')).weekday())
            week_availability = check_availability(events, current_week_start)
            embed = create_embed_for_week("Current Week", week_availability)
            await ctx.send(embed=embed)


@bot.command(name="disponible", description="Displays the availabilities of the person from the iCal file")
async def disponible(ctx, url: discord.Option(discord.SlashCommandOptionType.string),
                     person: discord.Option(discord.SlashCommandOptionType.string)):
    print("Command 'disponible' called")
    async with ctx.typing():
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ics') as temp_file:
            await download_ical(url, temp_file.name, ctx)
            if os.path.getsize(temp_file.name) == 0:
                await ctx.respond("The downloaded iCal file is empty.")
                return
            await register_user_ical(ctx.author.id, temp_file.name, user_icals)
            await is_person_available(temp_file.name, person, ctx)


@bot.command(name="disponibilites",
             description="Displays the availabilities of all persons who uploaded their iCal files")
async def disponibilites(ctx):
    print("Command 'disponibilites' called")
    async with ctx.typing():
        await is_everyone_available(ctx, user_icals)


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


# todo: remove streamer command, remove it from settings & streamers vars in stream_notifications.py


@bot.command(name="top10messages",
             description="Displays the top 10 users who sent the most messages today.")
async def top10messages(ctx, bots: discord.Option(discord.SlashCommandOptionType.boolean) = False):
    await ctx.respond("Calculating, this may take a moment...")

    message_counts = {}

    # Get current date in UTC
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
