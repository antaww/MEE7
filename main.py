import os
import tempfile

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from src.ft.ft1.recommandations import analyze_and_recommend
from src.ft.ft1.stream_notifications import check_streamers
from src.ft.ft2.planning import download_ical, process_ical
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
