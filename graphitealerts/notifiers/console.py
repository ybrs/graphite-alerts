from ..level import Level
from . import Notifier

class ConsoleNotifier(Notifier):
    """ this is just a dummy notifier for debug purposes """
    
    name = 'console'

    @classmethod
    def get_instance(cls, app, **kwargs):
        return cls(app.storage)

    def __init__(self, storage):
        self._storage = storage

    def notify(self, metric_name, rule, value):
        incident_key = "console_notification_%s" % metric_name
        description = "%s alerted because of rule: %s value is: %s " % (metric_name, rule.rule, value)
        alert_exists = self._storage._client.get(incident_key)
        if rule.level != Level.NOMINAL:
            print "ALERT: >>>>", description
            self._storage._client.set(incident_key, 1)            
        elif alert_exists:
            print "RESOLVED: >>>>", description
            self._storage._client.delete(incident_key)

