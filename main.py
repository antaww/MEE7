import os

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from src.ft.ft1.recommandations import analyze_and_recommend

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')


@bot.command(name="hi", description="Says hi")
async def say_hi(ctx):
    await ctx.respond(f"Hi, {ctx.author.mention}!")


# Tâche planifiée pour exécuter l'analyse et la recommandation toutes les X heures
@tasks.loop(hours=1)
async def scheduled_recommendation():
    channel_id = 1252165373827092493

    # Récupérer le channel Discord
    channel = bot.get_channel(channel_id)
    if channel:
        recommendation = await analyze_and_recommend(bot, channel_id)
        await channel.send(recommendation)


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


bot.run(DISCORD_BOT_TOKEN)
