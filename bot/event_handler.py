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
        if firebase.get('/glossary', key):
            return firebase.get('/glossary', key).itervalues().next()
        return False

    def _handle_message_change_event(self, event):
        if 'subtype' in event and event['subtype'] == 'message_changed':
            return event['message']
        else:
            return event


    def _handle_message(self, event):
        # Filter out messages from the bot itself
        if not self.clients.is_message_from_me(event['user']):

            event = self._handle_message_change_event(event)
            msg_txt = event['text']

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

                add_definition_regexp = re.search("^<@{}>[\s:]+(.+)\s*=\s*(.+)".format(re.escape(self.clients.bot_user_id())), msg_txt)
                get_definition_regexp = re.search("^<@{}>[\s:]+(.+)".format(re.escape(self.clients.bot_user_id())), msg_txt)
                
                self.clients.send_user_typing(event['channel'])
                
                if add_definition_regexp:
                    key = add_definition_regexp.group(1)
                    value = add_definition_regexp.group(2)
                    if self._save(key, value):
                        self.msg_writer.send_message(event['channel'], 'Saved `{}` as: ```{}```'.format(key, value))
                    else:
                        self.msg_writer.send_message(event['channel'], '`{}` already defined as: ```{}```'.format(key, self._get(key)))
                elif get_definition_regexp:
                    key = get_definition_regexp.group(1)
                    value = self._get(key)
                    if value:
                        self.msg_writer.send_message(event['channel'], 'Definition for `{}` is: ```{}```'.format(key, value))
                    else:
                        self.msg_writer.send_message(event['channel'], '`{}` is not defined yet. Use: `<@{}> {}=Definition text` to define'.format(key, self.clients.bot_user_id(), key))                
                else:
                    self.msg_writer.send_message(event['channel'], 'Wrong input')
