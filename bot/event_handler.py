from __future__ import print_function
import sys

import json
import logging
import re

logger = logging.getLogger(__name__)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class RtmEventHandler(object):
    def __init__(self, slack_clients, msg_writer):
        self.clients = slack_clients
        self.msg_writer = msg_writer

    def handle(self, event):

        if 'type' in event:
            self._handle_by_type(event['type'], event)

    def _handle_by_type(self, event_type, event):
        # See https://api.slack.com/rtm for a full list of events
        if event_type == 'error':
            # error
            self.msg_writer.write_error(event['channel'], json.dumps(event))
        elif event_type == 'message':
            # message was sent to channel
            self._handle_message(event)
        elif event_type == 'channel_joined':
            # you joined a channel
            self.msg_writer.write_help_message(event['channel'])
        elif event_type == 'group_joined':
            # you joined a private group
            self.msg_writer.write_help_message(event['channel'])
        else:
            pass

    def _save(self, key, value):
        from firebase import firebase
        firebase = firebase.FirebaseApplication('https://sweltering-inferno-3699.firebaseio.com', None)
        if firebase.get('/glossary', key):
            return False
        firebase.post('/glossary/' + key, value)
        return True

    def _get(self, key):
        from firebase import firebase
        firebase = firebase.FirebaseApplication('https://sweltering-inferno-3699.firebaseio.com', None)
        return firebase.get('/glossary', key)
        
    def _handle_message(self, event):
        # Filter out messages from the bot itself
        if not self.clients.is_message_from_me(event['user']):

            #eprint(event)
            
            #self._save('test', 'Test is testing')
            #self._get('test')

            msg_txt = event['text']
            eprint(msg_txt)

            if self.clients.is_bot_mention(msg_txt):
                # e.g. user typed: "@pybot tell me a joke!"
                '''if 'help' in msg_txt:
                    self.msg_writer.write_help_message(event['channel'])
                elif re.search('hi|hey|hello|howdy', msg_txt):
                    self.msg_writer.write_greeting(event['channel'], event['user'])
                elif 'joke' in msg_txt:
                    self.msg_writer.write_joke(event['channel'])
                elif 'attachment' in msg_txt:
                    self.msg_writer.demo_attachment(event['channel'])
                else:
                    self.msg_writer.write_prompt(event['channel'])'''

                if '=' in msg_txt:
                    (key, value) = msg_txt.split('=')
                    if self._save(key, value):
                        self.msg_writer.send_message(event['channel'], 'Saved {} as {}'.format(key, value))
                    else:
                        self.msg_writer.send_message(event['channel'], 'Already defined as:')
                        self.msg_writer.send_message(event['channel'], self._get(key))
                else:
                    if self._get(msg_txt):
                        self.msg_writer.send_message(event['channel'], self._get(msg_txt))
                    else:
                        self.msg_writer.send_message(event['channel'], 'Not defined yet')
