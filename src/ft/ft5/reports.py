import json
from datetime import datetime, timedelta, timezone

from src.utilities.utilities import get_current_date_formatted


class Reports:
    def __init__(self):
        self.messages_data = []
        self.load_messages()

    def add_message(self, message):
        self.messages_data.append({
            'author': message.author.id,
            'content': message.content,
            'timestamp': message.created_at.isoformat()
        })

    def get_messages(self):
        return self.messages_data

    def get_unique_authors(self):
        return set([message['author'] for message in self.messages_data])

    def load_messages(self):
        try:
            filename = f'src/ft/ft5/messages_{get_current_date_formatted()}.json'
            with open(filename, 'r') as file:
                self.messages_data = json.load(file)
        except FileNotFoundError:
            self.messages_data = []

    def save_messages(self):
        # Generate the filename based on the current date
        filename = f'src/ft/ft5/messages_{get_current_date_formatted()}.json'
        with open(filename, 'w') as file:
            json.dump(self.messages_data, file, indent=4)

    def is_spam(self, message):
        for stored_message in self.messages_data:
            stored_time = datetime.fromisoformat(stored_message['timestamp'])
            # Convert current UTC time to an offset-aware datetime
            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            if (stored_message['author'] == message.author.id and
                    stored_message['content'] == message.content and
                    stored_time >= (current_time - timedelta(days=1))):
                return True
        return False