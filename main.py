import discord
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')


@bot.command(name="hi", description="Says hi")
async def say_hi(ctx):
    await ctx.send(f"Hi, {ctx.author.mention}!")


bot.run(DISCORD_BOT_TOKEN)
