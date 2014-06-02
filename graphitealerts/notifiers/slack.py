import logging
import requests
import json
from ..level import Level
from . import Notifier

log = logging.getLogger('notifiers.hipchat')

class SlackNotifier(Notifier):

    name = 'slack'

    @classmethod
    def get_instance(cls, app, url, channel='#alerts', username='alertus', icon_emoji=':warning:', **kwargs):
        return cls(app, app.storage, url, channel, username, icon_emoji)

    def __init__(self, app, storage, url, channel, username, icon_emoji):
        self._storage = storage
        self.url = url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji
        log.info('Initializing SlackNotifier')

    def notify(self, alert_key, level, description, html_description):
        domain = 'slack'

        def _notify():
            payload = {"channel": self.channel,
                       "username": self.username,
                       "text": str(description),
                       "icon_emoji": self.icon_emoji}
            requests.post(self.url, dict(
                payload=json.dumps(payload)
            ))

        notified = self._storage.is_locked_for_domain_and_key(domain, alert_key)
        if level == Level.NOMINAL and notified:
            _notify()
            self._storage.remove_lock_for_domain_and_key(domain, alert_key)
        elif level in (Level.WARNING, Level.CRITICAL) and not notified:
            _notify()
            self._storage.set_lock_for_domain_and_key(domain, alert_key)
            log.debug('hipchat notification triggered for %s', alert_key)
