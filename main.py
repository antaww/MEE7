import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

bot = commands.Bot(command_prefix='$m ', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="hi", description="Say hi to the bot!")
async def _hi(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hi, {interaction.user.name}!")

bot.run(DISCORD_BOT_TOKEN)
