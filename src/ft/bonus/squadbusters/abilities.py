import json
import os

from loguru import logger


def generate_ultras(soup, api):
    ultras_data = {
        'description': "Ultra abilities are unlocked with the 4th evolution, which need a total of 1,000 babies. Each "
                       "troop evolved to Ultra gives 300 additional Portal Energy."
    }

    # Select all the sections containing character information
    sections = soup.select(
        "div.vp-doc._abilities_ultras h2, div.vp-doc._abilities_ultras img, div.vp-doc._abilities_ultras p")
    # Parse the sections to extract character information
    current_character = None
    for section in sections:
        strip = section.text.strip()
        if section.name == "h2":
            current_character = strip.replace(" ​", "")
            if 'Troop Index' in current_character:  # Skip the first section
                current_character = None
                continue
            ultras_data[current_character] = {}
            ultras_data[current_character]['name'] = strip.replace(" ​", "")
        elif section.name == "img" and current_character:
            if "portrait" in section['src']:
                ultras_data[current_character]['image'] = api + section['src']
        elif section.name == "p" and current_character:
            text = strip
            if 'description' not in ultras_data[current_character]:
                ultras_data[current_character]['description'] = text
            elif 'details' not in ultras_data[current_character]:
                ultras_data[current_character]['details'] = text

    # Format the abilities data
    abilities_data_formatted = {k.lower().replace(" ", "-"): v for k, v in ultras_data.items()}

    # Check if the file exists
    if os.path.exists("src/ft/bonus/squadbusters/abilities.json"):
        with open("src/ft/bonus/squadbusters/abilities.json", "r") as file:
            existing_data = json.load(file)

        # Compare existing data with new data
        if existing_data == abilities_data_formatted:
            logger.info('No new data to update in abilities.json')
            return

    # Write the new data if it's different
    logger.info('New data found, updating abilities.json')
    with open("src/ft/bonus/squadbusters/abilities.json", "w") as file:
        json.dump(abilities_data_formatted, file, indent=4)
        logger.success('Updated abilities.json')
