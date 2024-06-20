import json
import os

warnings_file = "warnings.json"


class Warnings:
    def __init__(self):
        if os.path.exists(warnings_file):
            self.load_warnings()
        else:
            self.warnings = {}

    def load_warnings(self):
        with open(warnings_file, "r") as f:
            self.warnings = json.load(f)

    def save_warnings(self):
        with open(warnings_file, "w") as f:
            json.dump(self.warnings, f, indent=4)

    def add_warning(self, user_id):
        user_id = str(user_id)
        if user_id in self.warnings:
            self.warnings[user_id] += 1
        else:
            self.warnings[user_id] = 1
        self.save_warnings()

    def get_user_warnings(self, user_id):
        # reload the warnings in case they were updated elsewhere
        self.load_warnings()
        return self.warnings.get(str(user_id), 0)

    def get_all_warnings(self, limit=10):
        # reload the warnings in case they were updated elsewhere
        self.load_warnings()
        return {k: v for k, v in sorted(self.warnings.items(), key=lambda item: item[1], reverse=True)[:limit]}

    def clear_warnings(self, user_id):
        if user_id in self.warnings:
            del self.warnings[user_id]
            self.save_warnings()
