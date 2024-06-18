from better_profanity import profanity

from src.ft.ft3.warnings import Warnings

warnings = Warnings()


async def handle_profanities(message):
    """
    This function handles messages that contain profanity.

    Args:
        message (discord.Message): The message that was sent in the channel.

    The function first checks if the message content contains any profanity using the `better_profanity` library. If
    the message contains profanity, it is deleted and a warning message is sent to the channel, mentioning the author
    of the message. The warning message is then deleted after a delay of 10 seconds.

    This function doesn't return anything.
    """
    if profanity.contains_profanity(message.content):  # Check if the message contains profanity.
        await message.delete()  # Delete the message.
        warnings.add_warning(message.author.id)
        warning_msg = await message.channel.send(
            f":warning: **{message.author.mention}**, your message has been deleted for __containing profanity__. "
            f"\n_Please keep the chat clean._")  # Send a warning message to the channel.
        await warning_msg.delete(delay=10)  # Delete the warning message after 10 seconds.
