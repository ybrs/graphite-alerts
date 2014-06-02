import logging
from ..level import Level
from . import Notifier
from pagerduty import PagerDuty


log = logging.getLogger('notifiers.pagerduty')

class PagerdutyNotifier(Notifier):
    
    name = 'pagerduty'

    @classmethod
    def get_instance(cls, app, key, **kwargs):
        client = PagerDuty(service_key=key)
        return cls(client, app.storage)

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        log.info('Initializing PagerdutyNotifier')

    def notify(self, alert_key, level, description, html_description):
        incident_key = self._storage.get_incident_key_for_alert_key(alert_key)
        if level != Level.NOMINAL:
            description = str(description)
            incident_key = self._client.trigger(incident_key=incident_key, description=description)
            self._storage.set_incident_key_for_alert_key(alert_key, incident_key)
            log.debug('pagerduty notification triggered for %s', alert_key)
        elif incident_key is not None:
            self._client.resolve(incident_key=incident_key)
            self._storage.remove_incident_for_alert_key(alert_key)        