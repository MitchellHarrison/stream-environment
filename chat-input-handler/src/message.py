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
            fr"badges=(?P<badges>[^;]*).*display-name=(?P<display_name>[^;]*).*emotes=(?P<emotes>[^;]*);.+user-id=(?P<user_id>[\d]+).+:(?P<username>[\d\w]+)![^:]+:(?P<text>.*)\r",
            flags=re.IGNORECASE
        )

        self.message_data = self.parse(self.message)
        self.text = self.message_data.get("message", "")
        self.sender = TwitchUser(
            self.message_data.get("user_id", ""),
            self.message_data.get("display_name", ""),
            self.get_badges(self.message_data.get("badges", ""))
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
            "username": message_data.get("username", ""),
            "message": message_data.get("text", ""),
            "badges": message_data.get("badges", "")
        }
        return output


    def get_badges(self, badges_str:str) -> list:
        badges = [badge.split("/")[0] for badge in badges_str.split(",")] 
        return badges


    def __repr__(self):
        return self.text
