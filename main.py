import json
import os
import tempfile
from datetime import datetime, timezone
from loguru import logger

import discord
import matplotlib.pyplot as plt
from discord.ext import tasks, commands
from dotenv import load_dotenv

from src.ft.bonus.squadbusters.navigation import NavigationView
from src.ft.ft1.recommendations import generate_recommendations
from src.ft.ft1.stream_notifications import check_streamers, validate_streamer
from src.ft.ft2.icals_to_json import register_user_ical, load_user_icals
from src.ft.ft2.planning import (
    is_everyone_available,
    download_ical,
    is_person_available,
    ensure_temp_dir,
    TEMP_DIR
)
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

user_icals = {}
load_user_icals()

@bot.event
async def on_ready():
    logger.success(f'Bot is ready. Logged in as {bot.user}')
    await handle_tasks()

async def handle_tasks():
    scheduled_recommendation.start()
    check_streamers.start(bot)
    scheduled_update.start()

@tasks.loop(hours=24)
async def scheduled_update():
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

@tasks.loop(hours=1)
async def scheduled_recommendation():
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
    channel_id = channel.id
    channel = bot.get_channel(channel_id)
    if channel:
        recommendation = await generate_recommendations(bot, channel, channel_id)
        await ctx.respond(recommendation)
    else:
        await ctx.respond("Channel not found for analysis.")

@bot.command(name="warnings", description="Displays the warnings for a user or all users")
async def display_warnings(ctx, user: discord.User = None):
    if user:
        await ctx.respond(f"{user.mention} has {warnings.get_user_warnings(user.id)} warning(s).")
    else:
        all_warnings = warnings.get_all_warnings()
        if all_warnings:
            description = "\n".join(
                [f"**{i + 1}**. {ctx.guild.get_member(int(user_id)).mention} - {count} warning(s)"
                 for i, (user_id, count) in enumerate(all_warnings.items())])
        else:
            description = "No warnings found."
        embed = discord.Embed(
            title=f":warning: Warnings Summary of {ctx.guild.name}",
            color=discord.Color.red(),
            description=description)
        embed.set_footer(text="MEE7 Warning System", icon_url=settings.get('icon_url'))
        await ctx.respond(embed=embed)

@bot.command(name="register_ical", description="Register your iCal file for availability checks")
async def register_ical(ctx, url: discord.Option(discord.SlashCommandOptionType.string)):
    ensure_temp_dir()
    temp_file_path = os.path.join(TEMP_DIR, 'temp.ics')
    await download_ical(url, temp_file_path, ctx)
    await register_user_ical(ctx.author.id, ctx.author.name, temp_file_path, user_icals)
    await ctx.respond(f":white_check_mark: Your iCal file has been registered successfully.")

@bot.command(name="disponibilites", description="Displays the availabilities of all persons who uploaded their iCal files")
async def disponibilites(ctx):
    async with ctx.typing():
        embeds = await is_everyone_available(ctx, "user_icals/kheir.json")
        for embed in embeds:
            await ctx.respond(embed=embed)

@bot.command(name="add_streamer", description="Adds a streamer to the list of streamers to check")
@commands.has_permissions(administrator=True)
async def add_streamer(ctx, streamer: discord.Option(discord.SlashCommandOptionType.string)):
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

    for channel in ctx.guild.text_channels:
        async for message in channel.history(limit=None, after=datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)):
            if message.author.bot and not bots:
                continue
            if message.author.id in message_counts:
                message_counts[message.author.id] += 1
            else:
                message_counts[message.author.id] = 1

    sorted_counts = sorted(message_counts.items(), key=lambda item: item[1], reverse=True)
    top10 = sorted_counts[:10]

    if not top10:
        embed = discord.Embed(
            title=f"No messages found today ({today})",
            description="No data available for top 10 users by message count.",
            color=discord.Color.blue())
        embed.set_footer(text="MEE7 Stats", icon_url=settings.get('icon_url'))
        await ctx.respond(embed=embed)
        return

    user_names = []
    message_numbers = []
    for user_id, count in top10:
        user = await bot.fetch_user(user_id)
        user_names.append(f"{user.name}#{user.discriminator}" if user.discriminator != "0" else user.name)
        message_numbers.append(count)

    plt.figure(figsize=(10, 5))
    plt.bar(user_names, message_numbers, color='skyblue')
    for i, v in enumerate(message_numbers):
        plt.text(i, v + 0.5, str(v), ha='center', va='bottom')
    plt.xlabel('Users')
    plt.ylabel('Message Count')
    plt.title(f"Top 10 Users by Message Count (Today, {today})")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('top10messages.png')
    plt.close()

    embed = discord.Embed(title=f"Top 10 Users by Message Count (Today, {today})", color=discord.Color.blue())
    embed.set_image(url="attachment://top10messages.png")
    embed.set_footer(text="MEE7 Stats", icon_url=settings.get('icon_url'))
    await ctx.respond(embed=embed, file=discord.File('top10messages.png'))
    os.remove('top10messages.png')

# @bot.command(name='sb-ultras', description='Display the list of ultra abilities')
# async def sb_ultras(ctx, character: Option(str, "The character name (Archer Queen, Barbarian...)", required=False)):
#     with open("src/ft/bonus/squadbusters/abilities.json", "r") as file:
#         abilities_data = json.load(file)
#     characters = [character for character in abilities_data.keys() if character != 'description']
#
#     if character:
#         character = character.lower().replace(" ", "-")
#         if character in abilities_data:
#             start_index = characters.index(character)
#         else:
#             await ctx.respond(f"Character {character} not found.")
#             return
#     else:
#         start_index = 0
#
#     view = NavigationView(characters, abilities_data, start_index)
#     embed = view.update_embed()
#     await ctx.respond(embed=embed, view=view)

setup_commands(bot)
bot.run(DISCORD_BOT_TOKEN)
