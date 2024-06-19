import json


class Settings:
    def __init__(self):
        with open('settings.json') as f:
            self.settings = json.load(f)

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        self.settings[key] = value
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)

    def add_streamer(self, streamer):
        streamers_list = self.settings.get('streamers_list', [])
        streamers_list.append(streamer)
        self.settings['streamers_list'] = streamers_list
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
