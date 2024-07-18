# 🎉 Welcome to MEE7 Bot! 


## 🤖 What is MEE7 Bot? 
MEE7 is a Discord bot that offers a variety of features to help you manage your Discord server and engage with your community. With MEE7, you can add streamers for live notifications, clean up chat messages, display common availability for scheduling, recommend content based on discussions, register iCal files for availability checks, and more.

MEE7 is designed to enhance your Discord server experience by providing useful tools and features to keep your community active, organized, and engaged. Whether you're a streamer, a content creator, or a community manager, MEE7 has something for everyone.

## MEE7 Bot Commands 

Welcome to the MEE7 Discord Bot command guide! Here are the commands for the MEE7 bot, along with their explanations to help you manage and engage with your community effectively.





<!-- TOC -->
* [MEE7 Bot Commands 🎉](#mee7-bot-commands-)
  * [Commands](#commands)
    * [📺 add_streamer](#-add_streamer)
    * [🧹 cleanup](#-cleanup)
    * [📆 display_common_availability](#-display_common_availability)
    * [📅 availability](#-availability)
    * [📢 recommend](#-recommend)
    * [📂 register_ical](#-register_ical)
    * [🎮 sb-ultras](#-sb-ultras)
    * [⚔️ raids](#-raids)
    * [🥇 top10messages](#-top10messages)
    * [⚠️ warnings](#-warnings)
  * [Contributing 🤝](#contributing-)
  * [Authors 📝](#authors-)
<!-- TOC -->

Let's explore the commands offered by MEE7 to help you make the most of your Discord server!

## Commands

### 📺 add_streamer

Description: Adds a streamer to the list of streamers to check for live notifications. 
- Usage: ```/add_streamer <streamer_name>```

### 🧹 cleanup
Description: Cleans up the last 10 messages in the channel to maintain a tidy chat environment.
- Usage: ```/cleanup```

### 📆 display_common_availability
Description: Displays the common availability of all users for the current week, helping to find the best times for group events.

- Usage: ```/display_common_availability```

### 📅 availability
Description: Displays the availabilities of all persons in the Discord server to facilitate scheduling and coordination.
- Usage: ```/availability```

### 📢 recommend
Description: Recommends content based on recent discussions to keep the community engaged with relevant topics.
- Usage: ```/recommend <channel>```

### 📂 register_ical
Description: Register your iCal file for availability checks to streamline event planning.
- Usage: ```/register_ical <iCal_link>```

### 🎮 sb-ultras
Description: Displays the list of ultra abilities, providing information on special commands or features.
- Usage: ```/sb-ultras <?character>```

### ⚔️ raids
Description: Displays the list of raids, providing information on upcoming raids and events.
- Usage: ```/raids```


### 🥇 top10messages
Description: Displays the top 10 users who sent the most messages today, encouraging active participation.
- Usage: ```/top10messages <?include_bots>```

### ⚠️ warnings
Description: Displays the warnings for a user or all users, helping to monitor and manage user behavior.
- Usage: ```/warnings <?user>```

With these commands, you can effectively manage your Discord community, keep the environment tidy, facilitate scheduling, and engage users with relevant content and activities. Enjoy your time with MEE7! 🎉

## Contributing 🤝
Contributions are welcome! If you'd like to add new features, improve existing ones, or fix bugs, feel free to create a pull request.

## Authors 📝
- [Anta](https://github.com/antaww)
- [Kerr](https://github.com/Mkheir13)

Transform your Discord server into a dynamic and well-managed community with MEE7! 🎊✨


## Configurations


Config .env file : 
```
DISCORD_BOT_TOKEN=your_discord_bot_token
TEXTRAZOR_API_KEY=your_textrazor_api_key
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TENOR_API_KEY=your_tenor_api_key
TENOR_CLIENT_KEY=your_tenor_client_key
GPT-EMAIL=your_gpt_email
GPT-PASSWORD=your_gpt_password
OPENWEATHER_API_KEY=your_openweather_api_key
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