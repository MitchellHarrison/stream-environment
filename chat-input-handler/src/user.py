class TwitchUser:
    def __init__(self, user_id:str, display_name:str, roles:list):
        self.user_id = user_id
        self.display_name = display_name
        self.username = self.display_name.lower()
        self.roles = roles

        self.is_broadcaster = "broadcaster" in roles
        self.is_mod = "mod" in roles

