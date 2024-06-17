import discord

def setup_commands(bot):
    @bot.command(name="cleanup", description="Nettoyer les messages")
    async def nettoyer_les_messages(ctx):
        try:
            # Purge les messages du bot
            deleted = await ctx.channel.purge()
            await ctx.send(f"{len(deleted)} messages supprimés.")
        except discord.Forbidden:
            await ctx.send("Je n'ai pas la permission de supprimer les messages.")
        except discord.HTTPException:
            await ctx.send("Une erreur s'est produite lors de la suppression des messages.")

