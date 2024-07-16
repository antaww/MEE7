import os
from re import search

import textrazor


async def analyze_topics(bot, channel_id):
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

    This function returns a string which is the recommendation message and a list of topics.
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
        return topics[:3]
    else:
        return []


async def recommend_article(query):
    """
    Asynchronously searches for and returns the first search result for a given query.

    This function performs an online search based on the provided query and attempts to return the URL of the first search result. If no results are found or an error occurs during the search, it handles these cases gracefully by returning a descriptive message.

    Args:
        query (str): The search query for which to find relevant articles.

    Returns:
        str: The URL of the first search result, a message indicating no results were found, or an error message.

    Raises:
        Exception: Captures and returns any exceptions as a string if an error occurs during the search process.
    """
    try:
        # Perform the search and get the results as a generator
        search_results = search(query, num_results=1)

        # Convert the generator to a list and get the first result
        search_results_list = list(search_results)

        # Return the first result if available
        if search_results_list:
            return search_results_list[0]
        else:
            return "No results found"
    except Exception as e:
        return f"An error occurred: {e}"


async def generate_recommendations(bot, channel, channel_id):
    """
    Generates and formats a set of recommendations based on the analysis of topics from recent discussions in a specified channel.

    This asynchronous function analyzes the topics of the last 100 messages in a given channel and then recommends articles related to the top 3 topics identified. It constructs a formatted message containing links to articles for each recommended topic.

    Args:
        bot: The bot instance used to interact with the Discord API.
        channel: The Discord channel object where the recommendations will be posted.
        channel_id: The ID of the channel for which to generate recommendations.

    Returns:
        A string containing the formatted recommendations. If no topics are found, a default message indicating no recommendations is returned.

    The function first calls `analyze_topics` to get the top topics from the channel's recent discussions. If topics are found, it iterates through the top 3 topics, calls `recommend_article` for each to find a related article, and appends this information to the recommendation message. The final message is then returned.
    """
    topics = await analyze_topics(bot, channel_id)
    recommendation = "No recommendations at this time."
    if topics:  # If there are any topics.
        recommendation = f"Here are some recommendations based on recent discussions in {channel.mention}:"
        for topic in topics[:3]:  # Get the top 3 topics.
            article = await recommend_article(topic)
            recommendation += f"\n> - **{topic}** - [Read more](<{article}>)"
    return recommendation
