import os
import textrazor

async def analyze_and_recommend(bot, channel_id):
    # Logic pour analyser les messages récents et recommander du contenu
    # Ici, nous utiliserons Textrazor pour analyser le contenu des messages.

    client = textrazor.TextRazor(os.getenv('TEXTRAZOR_API_KEY'), extractors=["topics"])
    client.set_entity_freebase_type_filters(["/organization/organization"])
    client.set_entity_dbpedia_type_filters(["Company"])

    # Récupérer les messages récents dans un canal spécifique (par exemple)
    channel = bot.get_channel(channel_id)
    messages = await channel.history(limit=100).flatten()  # Récupérer les 100 derniers messages
    print(messages)

    content = "\n".join([message.content for message in messages])

    response = client.analyze(content)

    # Récupérer les topics principaux
    topics = [topic.label for topic in response.topics()]

    # Construire la recommandation basée sur les topics identifiés
    if topics:
        recommendation = f"Here are some recommendations based on recent discussions in {channel.name}:"
        for topic in topics[:3]:  # Limiter à trois topics pour la recommandation
            recommendation += f"\n- {topic}"

        return recommendation
    else:
        return "No recommendations at this time."