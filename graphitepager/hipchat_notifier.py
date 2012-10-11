import os

class HipchatNotifier(object):

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        self._rooms = set()

    def notify(self, alert_key, level, description, html_description):
        if self._storage.can_get_lock_for_domain_and_key('HipChat', alert_key):
            for room in self._rooms:
                self._client.message_room(
                    room, 'Graphite-Pager', html_description, message_format='html')

    def add_room(self, room):
        self._rooms.add(room)
