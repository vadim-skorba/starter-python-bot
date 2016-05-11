
import logging
import re
import time

from slacker import Slacker
from slackclient import SlackClient

logger = logging.getLogger(__name__)


class SlackClients(object):
    def __init__(self, token):
        self.token = token

        # Slacker is a Slack Web API Client
        self.web = Slacker(token)

        # SlackClient is a Slack Websocket RTM API Client
        self.rtm = SlackClient(token)

    def bot_user_id(self):
        return self.rtm.server.login_data['self']['id']

    def is_message_from_me(self, user):
        return user == self.bot_user_id()

    def is_bot_mention(self, message):
        if re.search("@{}".format(self.bot_user_id()), message):
            return True
        else:
            return False

    def send_user_typing(self, channel_id):
        user_typing_json = {"type": "typing", "channel": channel_id}
        self.rtm.server.send_to_websocket(user_typing_json)
        
    def send_user_typing_pause(self, channel_id, sleep_time=3.0):
        self.send_user_typing(channel_id)
        time.sleep(sleep_time)
