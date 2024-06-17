from discord.ext import tasks

interval = 10  # seconds


@tasks.loop(seconds=interval)
async def scheduled_hi(bot):
    channel = bot.get_channel(1252165373827092493)
    await channel.send(f"this is a scheduled hi every {interval} seconds")