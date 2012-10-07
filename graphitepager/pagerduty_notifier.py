from pagerduty import PagerDuty

class PagerdutyNotifier(object):

    def __init__(self, pd_key, storage):
        self._storage = storage
        self._client = PagerDuty(pd_key)

    def nominal(self, alert, target, value):
        key = self._storage.get_incident_key_for_alert_and_record(alert, target)
        if key:
            self._storage.remove_incident_for_alert_and_record(alert, target)
            self._client.resolve(incident_key=key)

    def warning(self, alert, target, value):
        key = self._storage.get_incident_key_for_alert_and_record(alert, target)
        self._client.trigger(incident_key=key)

    def critical(self, alert, target, value):
        key = self._storage.get_incident_key_for_alert_and_record(alert, target)
        self._client.trigger(incident_key=key)
