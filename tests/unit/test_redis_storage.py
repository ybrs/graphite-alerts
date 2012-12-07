from unittest import TestCase
import json

from mock import patch, MagicMock
import redis


from graphitepager.redis_storage import RedisStorage
from graphitepager.alerts import Alert
from graphitepager.graphite_data_record import GraphiteDataRecord


class TestRedisStorage(TestCase):

    def setUp(self):
        self.r_url = 'Redis URL'
        self.redis = MagicMock(redis)
        self.client = self.redis.from_url()
        self.alert = 'ALERT!'
        self.domain = 'DOMAIN'
        self.record = MagicMock(GraphiteDataRecord)()
        self.alert_key = 'ALERT!-incident-key'
        self.lock_key = 'LOCK-{0}-{1}'.format(self.domain, self.alert)

        self.rs = RedisStorage(self.redis, self.r_url)

    def should_create_redis_client(self):
        self.redis.from_url.assert_called_with(self.r_url)


class TestRedisStorageGettingIncidentKey(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageGettingIncidentKey, self).setUp()

    def test_gets_redis_key_from_alert_and_record(self):
        self.client.get.return_value = None
        self.returned = self.rs.get_incident_key_for_alert_key(self.alert)
        self.client.get.assert_called_once_with(self.alert_key)

    def test_no_incident_in_redis(self):
        self.client.get.return_value = None
        self.returned = self.rs.get_incident_key_for_alert_key(self.alert)
        self.assertEqual(self.returned, None)

    def test_incident_in_redis(self):
        self.client.get.return_value = '{"incident": "INCIDENT"}'
        self.returned = self.rs.get_incident_key_for_alert_key(self.alert)
        self.assertEqual(self.returned, 'INCIDENT')


class TestRedisStorageSettingIncidentKey(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageSettingIncidentKey, self).setUp()
        self.returned = self.rs.set_incident_key_for_alert_key(self.alert, 'INCIDENT')
        self.value = json.dumps({'incident': 'INCIDENT'})

    def test_sets_redis_key_for_alert_and_record(self):
        self.client.set.assert_called_once_with(self.alert_key, self.value)

    def test_sets_key_to_expire(self):
        self.client.expire.assert_called_once_with(self.alert_key, 3600)


class TestRedisStorageRemovingIncidentKey(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageRemovingIncidentKey, self).setUp()
        self.returned = self.rs.remove_incident_for_alert_key(self.alert)

    def test_removes_redis_key_for_alert_and_record(self):
        self.client.delete.assert_called_once_with(self.alert_key)


class TestRedisStorageGettingLockWhenNoKey(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageGettingLockWhenNoKey, self).setUp()
        self.client.get.return_value = None
        self.returned = self.rs.is_locked_for_domain_and_key(self.domain, self.alert)

    def test_get_set_lock_key(self):
        self.client.get.assert_called_once_with(self.lock_key)

    def test_get_true_back(self):
        self.assertEqual(self.returned, False)


class TestRedisStorageGettingLockWhenThereIsAKey(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageGettingLockWhenThereIsAKey, self).setUp()
        self.client.get.return_value = True
        self.returned = self.rs.is_locked_for_domain_and_key(self.domain, self.alert)

    def test_get_set_lock_key(self):
        self.client.get.assert_called_once_with(self.lock_key)

    def test_get_true_back(self):
        self.assertEqual(self.returned, True)

class TestRedisStorageSettingLock(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageSettingLock, self).setUp()
        self.client.getset.return_value = 'Locked'
        self.returned = self.rs.set_lock_for_domain_and_key(self.domain, self.alert)

    def test_should_set_expiry(self):
        self.client.expire.assert_called_once_with(self.lock_key, 300)

    def test_set_lock(self):
        self.client.set.assert_called_once_with(self.lock_key, True)


class TestRedisStorageRemovingExistingLock(TestRedisStorage):

    def setUp(self):
        super(TestRedisStorageRemovingExistingLock, self).setUp()
        self.returned = self.rs.remove_lock_for_domain_and_key(self.domain, self.alert)

    def test_deletes_key(self):
        self.client.delete.assert_called_once_with(self.lock_key)
