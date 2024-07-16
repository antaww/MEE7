import json
import os

from src.utilities.utilities import get_current_date_formatted


class Warnings:
    def __init__(self):
        self.warnings_file = "src/ft/ft3/warnings.json"
        self.daily_warnings_file = f"src/ft/ft3/warnings_{get_current_date_formatted()}.json"
        self.warnings = {}
        self.daily_warnings = {}
        self.load_warnings()
        self.load_daily_warnings()

    def load_warnings(self):
        try:
            with open(self.warnings_file, "r") as f:
                self.warnings = json.load(f)
        except FileNotFoundError:
            self.warnings = {}
            self.save_warnings()

    def load_daily_warnings(self):
        try:
            with open(self.daily_warnings_file, "r") as f:
                self.daily_warnings = json.load(f)
        except FileNotFoundError:
            self.daily_warnings = {}
            self.save_warnings()

    def save_warnings(self):
        with open(self.warnings_file, "w") as f:
            json.dump(self.warnings, f, indent=4)
        with open(self.daily_warnings_file, "w") as f:
            json.dump(self.daily_warnings, f, indent=4)

    def add_warning(self, user_id):
        user_id = str(user_id)
        # Update global warnings
        if user_id in self.warnings:
            self.warnings[user_id] += 1
        else:
            self.warnings[user_id] = 1
        # Update daily warnings
        if user_id in self.daily_warnings:
            self.daily_warnings[user_id] += 1
        else:
            self.daily_warnings[user_id] = 1
        # Save both global and daily warnings
        self.save_warnings()

    def get_user_warnings(self, user_id):
        # Optionally, you might want to combine global and daily warnings here
        self.load_warnings()
        return self.warnings.get(str(user_id), 0)

    def get_all_warnings(self, limit=10):
        # Optionally, adjust to combine or separately handle daily warnings
        self.load_warnings()
        return {k: v for k, v in sorted(self.warnings.items(), key=lambda item: item[1], reverse=True)[:limit]}

    def get_all_daily_warnings(self, limit=10):
        # Optionally, adjust to combine or separately handle daily warnings
        self.load_daily_warnings()
        return {k: v for k, v in sorted(self.daily_warnings.items(), key=lambda item: item[1], reverse=True)[:limit]}

    def clear_warnings(self, user_id):
        user_id = str(user_id)
        # Clear from both global and daily warnings if present
        if user_id in self.warnings:
            del self.warnings[user_id]
        if user_id in self.daily_warnings:
            del self.daily_warnings[user_id]
        # Save changes
        self.save_warnings()
