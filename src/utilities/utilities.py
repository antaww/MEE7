import asyncio
from datetime import datetime

import re
import discord
from discord.ext import commands


def setup_commands(bot):
    @bot.command(name="cleanup", description="Cleans up the last 10 messages in the channel")
    @commands.has_permissions(manage_messages=True)
    async def cleanup(ctx):
        """
        This function is a command handler for the 'cleanup' command.

        Args:
            ctx (discord.Context): The context in which the command was called.

        The function first defers the response to avoid timeout. It then sends a confirmation message to the channel,
        asking the user if they want to delete the last 10 messages. The user can confirm or cancel the cleanup by
        reacting to the confirmation message with a check mark or a cross mark, respectively. If the user confirms
        the cleanup, the function deletes the last 10 messages in the channel and sends a message indicating the
        number of messages deleted. If the user cancels the cleanup or if the confirmation times out, the function
        sends a message indicating that the cleanup was canceled or timed out, respectively. If the bot does not have
        permission to delete messages or if an HTTP exception occurs, the function sends a message indicating the error.

        This function doesn't return anything.
        """
        try:
            await ctx.defer(ephemeral=True)  # Defer the response to avoid timeout

            async def confirm_cleanup(messages_cleaned=50, timeout=10):
                confirmation_embed = discord.Embed(
                    title="Confirm Cleanup",
                    description=f"Are you sure you want to __delete__ the last **{messages_cleaned} messages** in this channel? "
                                f"\n:hourglass: _{timeout}s remaining..._",
                    color=discord.Color.orange()
                )
                confirmation_embed.set_footer(text=f"Requested by {ctx.author.display_name}")

                # Send the confirmation message
                confirm_message = await ctx.send(embed=confirmation_embed, delete_after=timeout)

                # Add reactions for confirmation
                await confirm_message.add_reaction("✅")  # Check mark for confirmation
                await confirm_message.add_reaction("❌")  # Cross mark for cancellation

                # Define a check function to verify reactions
                def reaction_check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

                # Wait for user reaction
                try:
                    reaction, _ = await bot.wait_for("reaction_add", timeout=timeout, check=reaction_check)

                    # Process user reaction
                    if str(reaction.emoji) == "✅":
                        deleted = await ctx.channel.purge(limit=messages_cleaned)
                        await ctx.send(f":white_check_mark: {len(deleted)} messages deleted.", delete_after=timeout / 2)
                    else:
                        await ctx.send(":x: Cleanup canceled.", delete_after=timeout / 2)

                except asyncio.TimeoutError:
                    await ctx.send(":x: Cleanup confirmation timed out. Please try again.", delete_after=timeout / 2)

            # Call the confirmation function
            await confirm_cleanup()

        except discord.Forbidden:
            await ctx.send(":x: I don't have permission to delete messages.")
        except discord.HTTPException:
            await ctx.send(":x: Failed to delete messages.")


def get_current_date_formatted(separator=""):
    # Get the current date in the specified format (monthdayyear)
    return datetime.now().strftime(f"%m{separator}%d{separator}%Y")


def remove_non_bmp(text):
    return re.sub(r'[^\u0000-\uFFFF]', '', text)
