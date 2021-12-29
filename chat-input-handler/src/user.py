import colorsys
import random

TWITCH_PURPLE = (145, 70, 255)
 
class TwitchUser:
    def __init__(self, user_id="", display_name="", roles=[], color=""):
        self.user_id = user_id
        self.display_name = display_name
        self.username = self.display_name.lower()
        self.roles = roles
        self.is_broadcaster = "broadcaster" in roles
        self.is_mod = "mod" in roles

        # set color if user has chosen a custom color in settings
        if color:
            r,g,b = tuple(int(color[i:i+2], 16) for i in (1,3,5))
            h,s,v = colorsys.rgb_to_hsv(r,g,b)
            self.color = (r,g,b)
            if s < .55 and v < 50:
                self.color = TWITCH_PURPLE
            elif s < .66 and v < 62:
                self.color = TWITCH_PURPLE
            elif s <.78 and v < 73:
                self.color = TWITCH_PURPLE
            elif s < .85 and v < 80:
                self.color = TWITCH_PURPLE
            elif s > .9 and v < 90:
                self.color = TWITCH_PURPLE
        else:
            self.color = TWITCH_PURPLE
