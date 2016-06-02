from __future__ import print_function
import sys
import os

import json
import logging
import re
import urllib
import hashlib

from firebase import firebase

logger = logging.getLogger(__name__)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class RtmEventHandler(object):
    def __init__(self, slack_clients, msg_writer):
        self.clients = slack_clients
        self.msg_writer = msg_writer
        self.firebase = firebase.FirebaseApplication(os.getenv("FIREBASE_URL"), None)
        self.firebase.authentication = firebase.FirebaseAuthentication(os.getenv("FIREBASE_SECRET"), os.getenv("FIREBASE_EMAIL"))

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
        preparedKey = self._prepare_key(key)
        if preparedKey:
            eprint(preparedKey)
            eprint(self._get(key))
            if self._get(key):
                return False
            self.firebase.post('/glossary/' + preparedKey, value)
            return True
        else:
            return False

    def _get(self, key):
        preparedKey = self._prepare_key(key)
        if preparedKey:
            result = self.firebase.get('/glossary', preparedKey)
            eprint(result)
            if result:
                return result.itervalues().next()
        return False

    def _get_all(self, key):
        preparedKey = self._prepare_key(key)
        if preparedKey:
            return self.firebase.get('/glossary', preparedKey)
        return False

    def _clean_links(self, message):
        return re.sub("<([^@\#\!].*?)(\|.*?)?>", r'\1', message)

    def _prepare_key(self, key):
        hash_object = hashlib.md5(key.lower().encode('utf-8'))
        hash_string = hash_object.hexdigest()
        return hash_string

    def _is_hidden_message_event(self, event):
        return 'hidden' in event and event['hidden'] == True

    def _handle_message(self, event):
        # Filter out messages from the bot itself
        if not self._is_hidden_message_event(event) and not self.clients.is_message_from_me(event['user']):

            msg_txt = event['text']

            if self.clients.is_bot_mention(msg_txt):

                #if re.search("^<@{}>[\s:]+alllll$".format(re.escape(self.clients.bot_user_id())), msg_txt):
                    #return self.msg_writer.send_message(event['channel'], json.dumps(event))
                    #return self.msg_writer.send_message(ch, json.dumps(self._get_all(key)))

                add_definition_regexp = re.search("^<@{}>[\s:]+(.+)\s*=\s*(.+)".format(re.escape(self.clients.bot_user_id())), msg_txt, re.MULTILINE|re.DOTALL)
                get_definition_regexp = re.search("^<@{}>[\s:]+(.+)".format(re.escape(self.clients.bot_user_id())), msg_txt, re.MULTILINE|re.DOTALL)
                
                self.clients.send_user_typing(event['channel'])
                
                if add_definition_regexp:
                    key = add_definition_regexp.group(1)
                    value = add_definition_regexp.group(2)
                    value = self._clean_links(value)
                    if self._save(key, value):
                        self.msg_writer.send_message(event['channel'], u'Saved `{}` as: ```{}```'.format(key, value))
                    else:
                        self.msg_writer.send_message(event['channel'], u'`{}` already defined as: ```{}```'.format(key, self._get(key)))
                elif get_definition_regexp:
                    key = get_definition_regexp.group(1)
                    value = self._get(key)
                    if value:
                        self.msg_writer.send_message(event['channel'], u'Definition for `{}` is: ```{}```'.format(key, value))
                    else:
                        self.msg_writer.send_message(event['channel'], u'`{}` is not defined yet. Use: `<@{}> {}=Definition text` to define'.format(key, self.clients.bot_user_id(), key))                
                else:
                    self.msg_writer.send_message(event['channel'], u'Wrong input')
