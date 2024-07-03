Config .env file : 
```
DISCORD_BOT_TOKEN=your_discord_bot_token
TEXTRAZOR_API_KEY=your_textrazor_api_key
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TENOR_API_KEY=your_tenor_api_key
TENOR_CLIENT_KEY=your_tenor_client_key
```

How to get tenor api key & client key : https://developers.google.com/tenor/guides/quickstart

If new lib, update requirements.txt file:
```
pip-chill > requirements.txt
```

Error with : fr-core-news-sm
```
pip install spacy
python -m spacy download fr_core_news_sm
```