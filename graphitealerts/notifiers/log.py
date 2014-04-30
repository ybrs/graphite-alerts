import logging
from ..level import Level

log = logging.getLogger('notifiers.log')

class LogNotifier(object):
    '''
    This notifier logs to a file
    '''
    
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
