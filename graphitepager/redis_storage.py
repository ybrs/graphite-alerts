import json

class RedisStorage(object):

    def __init__(self, redis_lib, url):
        self._client = redis_lib.from_url(url)

    def get_incident_key_for_alert_and_record(self, alert, record):
        key = _redis_key_from_alert_and_record(alert, record)
        resp = self._client.get(key)
        if resp is not None:
            return json.loads(resp)['incident']

    def set_incident_key_for_alert_and_record(self, alert, record, ik):
        data = {'incident': ik}
        key = _redis_key_from_alert_and_record(alert, record)
        self._client.set(key, json.dumps(data))
        self._client.expire(key, 300)

    def remove_incident_for_alert_and_record(self, alert, record):
        key = _redis_key_from_alert_and_record(alert, record)
        self._client.delete(key)


def _redic_key_from_alert_and_target(alert, target):
    return '{0} {1}'.format(alert, record)


def _redis_key_from_alert_and_record(alert, record):
    return '{0} {1}'.format(alert.name, record.target)
