import os
from level import Level

class HipchatNotifier(object):

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        self._rooms = set()

    def notify(self, alert_key, level, description, html_description):
        colors = {
            Level.NOMINAL: 'green',
            Level.WARNING: 'yellow',
            Level.CRITICAL: 'red',
        }
        color = colors.get(level, 'red')
        domain = 'HipChat'
        notified = self._storage.is_locked_for_domain_and_key(domain, alert_key)
        if level == Level.NOMINAL and notified:
            for room in self._rooms:
                self._client.message_room(
                    room,
                    'Graphite-Pager',
                    html_description,
                    message_format='html',
                    color=color,
                )
            self._storage.remove_lock_for_domain_and_key(domain, alert_key)
        elif level in (Level.WARNING, Level.CRITICAL) and not notified:
            for room in self._rooms:
                self._client.message_room(
                    room,
                    'Graphite-Pager',
                    html_description,
                    message_format='html',
                    color=color,
                )
            self._storage.set_lock_for_domain_and_key(domain, alert_key)

    def add_room(self, room):
        self._rooms.add(room)
