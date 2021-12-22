import random

class TwitchUser:
    def __init__(self, user_id="", display_name="", roles=[], color=""):
        self.user_id = user_id
        self.display_name = display_name
        self.username = self.display_name.lower()
        self.roles = roles
        self.is_broadcaster = "broadcaster" in roles
        self.is_mod = "mod" in roles

        # default color to twitch purple
        default_color = tuple(random.randint(80,200) for i in range(3))
        # set color if user has chosen a custom color in settings
        if color:
            self.color = tuple(int(color[i:i+2], 16) for i in (1,3,5))
        else:
            self.color = default_color
