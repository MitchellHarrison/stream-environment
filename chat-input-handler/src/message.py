import re
import json
from datetime import datetime
from user import TwitchUser

COMMAND_TRIGGER = "!"

class TwitchMessage:
    def __init__(self, sent_time:str, message:str) -> None:
        self.sent_time = sent_time
        self.message = message
        self.twitch_pattern = re.compile(
            fr"badges=(?P<badges>[^;]*).*color=(?P<color>[^;]*).*display-name=(?P<display_name>[^;]*).*emotes=(?P<emotes>[^;]*);.+;id=(?P<message_id>[^;]*);.+user-id=(?P<user_id>[\d]+).*tv\sPRIVMSG\s(?P<channel>[^;]*)\s:(?P<text>.*)",
            flags=re.IGNORECASE
        )

        self.message_data = self.parse(self.message)
        self.text = self.message_data.get("message", "")
        self.sender = TwitchUser(
            self.message_data.get("user_id", ""),
            self.message_data.get("display_name", ""),
            self.get_badges(self.message_data.get("badges", "")),
            self.message_data.get("color", "")
        )

        self.is_command = False
        self.command = ""
        if self.text.startswith(COMMAND_TRIGGER):
            self.is_command = True
            self.command = self.text.split()[0]


    def parse(self, message:str) -> dict:
        message_data = {}
        try:
            message_data = self.twitch_pattern.search(message).groupdict() 
        except AttributeError:
            pass

        output = {
            "user_id": message_data.get("user_id", ""),
            "display_name": message_data.get("display_name", ""),
            "message": message_data.get("text", ""),
            "badges": message_data.get("badges", ""),
            "color": message_data.get("color", "")
        }
        return output


    def display(self) -> None:
        r,g,b = self.sender.color
        print(f"\033[38;2;{r};{g};{b}m" + self.sender.display_name + 
                "\033[38;2;255;255;255m", f"{self.text}\n")


    def get_badges(self, badges_str:str) -> list:
        badges = [badge.split("/")[0] for badge in badges_str.split(",")] 
        return badges


    def __repr__(self):
        return self.text
