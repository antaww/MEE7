import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$m7 ', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    # analyze_discussions.start()  # Démarrer la tâche planifiée pour les recommandations de contenu

@bot.command()
async def hi(ctx):
    await ctx.send('hi!')

bot.run(DISCORD_BOT_TOKEN)
