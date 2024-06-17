import os

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from src.ft.ft1.recommandations import analyze_and_recommend
from src.ft.ft1.stream_notifications import check_streamers

from src.utilities.utilities import setup_commands

# from src.tests.tests import scheduled_hi

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

bot = discord.Bot()


@bot.event
async def on_ready():
    # Planification de la tâche de vérification des streamers toutes les 5 minutes
    print(f'Bot is ready. Logged in as {bot.user}')
    scheduled_check_streamers.start()
    check_streamers.start(bot)
    # scheduled_hi.start(bot)


# Tâche planifiée pour exécuter l'analyse et la recommandation toutes les X heures
@tasks.loop(hours=1)
async def scheduled_recommendation():
    channel_id = 1252165373827092493

    # Récupérer le channel Discord
    channel = bot.get_channel(channel_id)
    if channel:
        # print(f"Analyzing and recommending content in {channel.name}")
        await channel.send(f"> # :alarm_clock: **Scheduled recommendation**\n> Analyzing and recommending content in {channel.name}...")
        recommendation = await analyze_and_recommend(bot, channel_id)
        await channel.send(recommendation)


@tasks.loop(minutes=5)
async def scheduled_check_streamers():
    await check_streamers(bot)


@bot.command(name="recommend", description="Recommends content based on recent discussions")
async def recommend(ctx, channel_id: discord.Option(discord.SlashCommandOptionType.string)):
    # check if channel_id is int
    if channel_id.isdigit():
        channel_id = int(channel_id)
        if bot.get_channel(channel_id):
            recommendation = await analyze_and_recommend(bot, channel_id)
            await ctx.respond(recommendation)
        else:
            await ctx.respond("Channel not found for analysis.")
    else:
        await ctx.respond("Invalid channel ID.")


setup_commands(bot)


bot.run(DISCORD_BOT_TOKEN)
