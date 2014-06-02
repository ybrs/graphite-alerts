import logging
from ..level import Level
from . import Notifier

log = logging.getLogger('notifiers.log')

class LogNotifier(Notifier):
    '''
    This notifier logs to a file
    '''
    name = 'log'

    @classmethod
    def getinstance(cls, app, *args, **kwargs):
        return cls(app.storage)

    def __init__(self, storage):
        self._storage = storage
        log.info('Initializing LogNotifier')

    def notify(self, alert_key, level, description, html_description):
        incident_key = "console_notification_%s" % alert_key
        alert_exists = self._storage._client.get(incident_key)
        if level != Level.NOMINAL:        
            description = str(description)
            if level == Level.CRITICAL:
              log.critical('ALERT %s %s %s', alert_key, level, description)
            else:
              log.warning('ALERT %s %s %s', alert_key, level, description)
            self._storage._client.set(incident_key, 1)            
        elif alert_exists:
            log.info('RESOLVED %s %s %s', alert_key, level, description)
            self._storage._client.delete(incident_key)
