from ..level import Level


class ConsoleNotifier(object):
    """ this is just a dummy notifier for debug purposes """
    
    name = 'console'
    
    def __init__(self, storage):
        self._storage = storage

    def notify(self, alert_key, level, description, html_description):
        incident_key = "console_notification_%s" % alert_key 
        alert_exists = self._storage._client.get(incident_key)
        if level != Level.NOMINAL:        
            description = str(description)
            print "ALERT: >>>>", alert_key, level, description, html_description            
            self._storage._client.set(incident_key, 1)            
        elif alert_exists:
            print "RESOLVED: >>>>", alert_key, level, description, html_description
            self._storage._client.delete(incident_key)
