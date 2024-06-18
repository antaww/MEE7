import asyncio

import discord

def setup_commands(bot):
    @bot.command(name="cleanup", description="Nettoyer les messages")
    async def nettoyer_les_messages(ctx):
        try:
            # delete last 10 messages
            deleted = await ctx.channel.purge(limit=10)
            await ctx.send(f"{len(deleted)} messages supprimés.")
            await asyncio.sleep(5)
            message = await ctx.channel.history().get(content=f"{len(deleted)} messages supprimés.")
            await message.delete()
        except discord.Forbidden:
            await ctx.send("Je n'ai pas la permission de supprimer les messages.")
        except discord.HTTPException:
            await ctx.send("Une erreur s'est produite lors de la suppression des messages.")

