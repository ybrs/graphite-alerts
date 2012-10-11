import json

class RedisStorage(object):

    def __init__(self, redis_lib, url):
        self._client = redis_lib.from_url(url)

    def get_incident_key_for_alert_key(self, alert):
        key = _redis_key_from_alert_key(alert)
        resp = self._client.get(key)
        if resp is not None:
            return json.loads(resp)['incident']

    def set_incident_key_for_alert_key(self, alert, ik):
        data = {'incident': ik}
        key = _redis_key_from_alert_key(alert)
        self._client.set(key, json.dumps(data))
        self._client.expire(key, 300)

    def remove_incident_for_alert_key(self, alert):
        key = _redis_key_from_alert_key(alert)
        self._client.delete(key)

    def set_lock_for_domain_and_key(self, domain, key):
        key = 'LOCK-{0}-{1}'.format(domain, key)
        self._client.set(key, True)
        self._client.expire(key, 300)

    def remove_lock_for_domain_and_key(self, domain, key):
        key = 'LOCK-{0}-{1}'.format(domain, key)
        self._client.delete(key)

    def is_locked_for_domain_and_key(self, domain, key):
        key = 'LOCK-{0}-{1}'.format(domain, key)
        value = self._client.get(key)
        if value is None:
            return False
        return True


def _redis_key_from_alert_key(alert_key):
    return '{0}-incident-key'.format(alert_key)
