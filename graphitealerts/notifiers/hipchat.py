import logging
from ..level import Level

log = logging.getLogger('notifiers.hipchat')

class HipchatNotifier(object):

    name = 'hipchat'

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        self._rooms = set()
        log.info('Initializing HipchatNotifier')

    def notify(self, alert_key, level, description, html_description):
        colors = {
            Level.NOMINAL: 'green',
            Level.WARNING: 'yellow',
            Level.CRITICAL: 'red',
        }
        color = colors.get(level, 'red')
        domain = 'HipChat'

        def _notify():
            description = str(html_description)
            self._notify_room_with_args(
                'Graphite-Pager',
                description,
                message_format='html',
                color=color,
            )

        notified = self._storage.is_locked_for_domain_and_key(domain, alert_key)
        if level == Level.NOMINAL and notified:
            _notify()
            self._storage.remove_lock_for_domain_and_key(domain, alert_key)
        elif level in (Level.WARNING, Level.CRITICAL) and not notified:
            _notify()
            self._storage.set_lock_for_domain_and_key(domain, alert_key)
            log.debug('hipchat notification triggered for %s', alert_key)

    def _notify_room_with_args(self, *args, **kwargs):
        for room in self._rooms:
            self._client.message_room(room, *args, **kwargs)

    def add_room(self, room):
        self._rooms.add(room)