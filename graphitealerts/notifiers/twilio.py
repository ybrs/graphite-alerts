import logging
from ..level import Level
from . import Notifier

log = logging.getLogger('notifiers.twilio')

class TwilioCallNotifier(Notifier):
    name = 'twilio_call'

    @classmethod
    def get_instance(cls, app, **kwargs):
        return cls({}, app.storage)

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        log.info('Initializing TwilioNotifier')

    def notify(self, alert_key, level, description, html_description):
        incident_key = self._storage.get_incident_key_for_alert_key(alert_key)
        if level != Level.NOMINAL:
            description = str(description)
            incident_key = self._client.trigger(incident_key=incident_key,
                                                description=description)
            self._storage.set_incident_key_for_alert_key(alert_key, incident_key)
            log.debug('pagerduty notification triggered for %s', alert_key)
        elif incident_key is not None:
            self._client.resolve(incident_key=incident_key)
            self._storage.remove_incident_for_alert_key(alert_key)

class TwilioSmsNotifier(Notifier):

    name = 'twilio_sms'

    @classmethod
    def get_instance(cls, app, **kwargs):
        return cls({}, app.storage)

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        log.info('Initializing TwilioNotifier')

    def notify(self, alert_key, level, description, html_description):
        incident_key = self._storage.get_incident_key_for_alert_key(alert_key)
        if level != Level.NOMINAL:
            description = str(description)
            incident_key = self._client.trigger(incident_key=incident_key,
                                                description=description)
            self._storage.set_incident_key_for_alert_key(alert_key, incident_key)
            log.debug('pagerduty notification triggered for %s', alert_key)
        elif incident_key is not None:
            self._client.resolve(incident_key=incident_key)
            self._storage.remove_incident_for_alert_key(alert_key)