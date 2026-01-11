import json
import os
from datetime import datetime


class UserStore:
    def __init__(self, file_path="user_data.json"):
        self.file_path = file_path
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    self.data = json.load(f)
                except json.JSONDecodeError:
                    self.data = {"profile": {}, "logs": []}
        else:
            self.data = {"profile": {}, "logs": []}
            self._save_data()

    def _save_data(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def update_profile(self, key: str, value):
        """Updates user profile information."""
        self.data["profile"][key] = value
        self._save_data()

    def get_profile(self):
        """Returns the user profile."""
        return self.data["profile"]

    def log_event(self, event: str):
        """Logs an event with a timestamp."""
        entry = {"timestamp": datetime.now().isoformat(), "event": event}
        self.data["logs"].append(entry)
        self._save_data()
