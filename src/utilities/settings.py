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