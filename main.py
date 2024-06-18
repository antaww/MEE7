import os
import tempfile

import discord
import nltk
from discord.ext import tasks
from dotenv import load_dotenv

from src.ft.ft1.recommandations import analyze_and_recommend
from src.ft.ft1.stream_notifications import check_streamers
from src.ft.ft4.gifs import search_gif
from src.ft.ft4.keywords import extract_keywords
from src.ft.ft4.sentiments import analyze_sentiment
from src.ft.ft2.planning import download_ical, process_ical
from src.utilities.settings import Settings

from src.utilities.utilities import setup_commands

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)
settings = Settings()



@bot.event
async def on_ready():
    """
    This function is an event handler that gets triggered when the bot is ready.
    This function doesn't take any arguments and doesn't return anything.
    """
    print(f'Bot is ready. Logged in as {bot.user}')
    scheduled_recommendation.start()
    check_streamers.start(bot)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild.id != 1252165373256794185:
        print(f"Message from {message.guild.name}")
        return

    if message.channel.id != settings.get('gifs_channel_id'):
        return

    sentiment = analyze_sentiment(message.content)
    keywords = extract_keywords(message.content)
    print(f"{sentiment} - {keywords}")
    gif_url = search_gif(f"{keywords}")
    print(f"GIF URL: {gif_url}")

    if gif_url:
        embed = discord.Embed()
        embed.set_image(url=gif_url)
        await message.channel.send(embed=embed)


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
        await channel.send(
            f"> # :alarm_clock: **Scheduled recommendation**\n> Analyzing and recommending content in {channel.name}..."
        )
        recommendation = await analyze_and_recommend(bot, channel_id)
        await channel.send(recommendation)


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


@bot.command(name="planning", description="Affiche le planning")
async def planning(ctx, url: discord.Option(discord.SlashCommandOptionType.string)):
    """
    This function is a command handler for the 'planning' command.

    It takes two arguments:
    - ctx: The context in which the command was called.
    - url: The URL of the iCal file to download.

    The function downloads the iCal file and sends the events of the current week as a message.
    """
    async with ctx.typing():
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ics') as temp_file:
            await download_ical(url, temp_file.name)
            await process_ical(temp_file.name, ctx)

setup_commands(bot)

bot.run(DISCORD_BOT_TOKEN)
