from ..level import Level


class PagerdutyNotifier(object):
    
    name = 'pagerduty'
    
    def __init__(self, client, storage):
        self._client = client
        self._storage = storage

    def notify(self, alert_key, level, description, html_description):
        incident_key = self._storage.get_incident_key_for_alert_key(alert_key)
        if level != Level.NOMINAL:
            description = str(description)
            incident_key = self._client.trigger(incident_key=incident_key, description=description)
            self._storage.set_incident_key_for_alert_key(alert_key, incident_key)
        elif incident_key is not None:
            self._client.resolve(incident_key=incident_key)
            self._storage.remove_incident_for_alert_key(alert_key)
