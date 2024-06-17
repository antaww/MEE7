import os
import textrazor


async def analyze_and_recommend(bot, channel_id):
    """
    This function analyzes the recent discussions in a given channel and recommends topics based on the analysis.

    It takes two arguments:
    - bot: The bot instance.
    - channel_id: The ID of the channel for which to analyze discussions and recommend topics.

    The function first initializes a TextRazor client with the API key and sets the entity filters.
    It then retrieves the channel using the channel_id and gets the last 100 messages from the channel.
    The content of these messages is joined into a single string and analyzed using the TextRazor client.

    The topics from the analysis are then retrieved and if there are any topics, a recommendation message is
    constructed and returned. The recommendation message includes the name of the channel and the top 3 topics. If
    there are no topics, a message indicating that there are no recommendations at this time is returned.

    This function returns a string which is the recommendation message.
    """
    client = textrazor.TextRazor(os.getenv('TEXTRAZOR_API_KEY'), extractors=["topics"])
    client.set_entity_freebase_type_filters(["/organization/organization"])
    client.set_entity_dbpedia_type_filters(["Company"])

    channel = bot.get_channel(channel_id)
    messages = await channel.history(limit=100).flatten()  # Get the last 100 messages from the channel.

    content = "\n".join([message.content for message in messages])

    response = client.analyze(content)  # Analyze the content using the TextRazor client.

    topics = [topic.label for topic in response.topics()]  # Retrieve the topics from the analysis.

    if topics:  # If there are any topics.
        recommendation = f"Here are some recommendations based on recent discussions in {channel.name}:"
        for topic in topics[:3]:  # Get the top 3 topics.
            recommendation += f"\n> - **{topic}**"

        return recommendation
    else:
        return "No recommendations at this time."
