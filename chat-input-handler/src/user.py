import colorsys
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
        default_color = (145, 70, 255)
        # set color if user has chosen a custom color in settings
        if color:
            r,g,b = tuple(int(color[i:i+2], 16) for i in (1,3,5))
            h,s,v = colorsys.rgb_to_hsv(r,g,b)
            if s < .55 and v < .5:
                self.color = default_color
            elif s < .66 and v < .62:
                self.color = default_color
            elif s <.78 and v < .73:
                self.color = default_color
            elif s < .85 and v < .8:
                self.color = default_color
            elif s > .9 and v < .9:
                self.color = default_color
            else:
                self.color = (r,g,b)
        else:
            self.color = default_color
