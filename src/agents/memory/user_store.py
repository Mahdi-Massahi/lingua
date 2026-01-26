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
        self.data["profile"][key] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
        }
        self._save_data()

    def get_profile(self):
        """Returns the user profile."""
        return self.data["profile"]

    def log_event(self, event: str):
        """Logs an event with a timestamp."""
        entry = {"timestamp": datetime.now().isoformat(), "event": event}
        self.data["logs"].append(entry)
        self._save_data()

    def update_streak(self):
        """Updates the user's activity streak."""
        profile = self.data["profile"]
        today = datetime.now().strftime("%Y-%m-%d")
        last_active = profile.get("last_active_date")
        current_streak = profile.get("current_streak", 0)
        max_streak = profile.get("max_streak", 0)

        if last_active == today:
            return  # Already counted today

        if last_active:
            last_date = datetime.strptime(last_active, "%Y-%m-%d")
            delta = (datetime.now() - last_date).days
            if delta == 1:
                current_streak += 1
            elif delta > 1:
                current_streak = 1
        else:
            current_streak = 1

        if current_streak > max_streak:
            max_streak = current_streak

        profile["last_active_date"] = today
        profile["current_streak"] = current_streak
        profile["max_streak"] = max_streak
        self._save_data()
