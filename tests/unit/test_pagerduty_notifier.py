from unittest import TestCase


from mock import patch, MagicMock
from pagerduty import PagerDuty

from graphitepager.pagerduty_notifier import PagerdutyNotifier
from graphitepager.redis_storage import RedisStorage
from graphitepager.level import Level


class TestPagerduteryNotifier(TestCase):

    def setUp(self):
        self.alert_key = 'ALERT KEY'
        self.description = 'ALERT DESCRIPTION'
        self.html_description = 'HTML ALERT DESCRIPTION'
        self.mock_redis_storage = MagicMock(RedisStorage)
        self.mock_pagerduty_client = MagicMock(PagerDuty)

        self.pn = PagerdutyNotifier(self.mock_pagerduty_client, self.mock_redis_storage)

    def test_should_trigger_with_warning_level_and_key(self):
        incident_key = 'KEY'
        self.mock_redis_storage.get_incident_key_for_alert_key.return_value = incident_key

        self.pn.notify(self.alert_key, Level.WARNING, self.description, self.html_description)

        self.mock_redis_storage.get_incident_key_for_alert_key.assert_called_once_with(self.alert_key)
        self.mock_pagerduty_client.trigger.assert_called_once_with(
            incident_key=incident_key, description=self.description)
        self.mock_redis_storage.set_incident_key_for_alert_key.assert_called_once_with(
            self.alert_key, self.mock_pagerduty_client.trigger())

    def test_should_trigger_with_warning_level_and_no_key(self):
        self.mock_redis_storage.get_incident_key_for_alert_key.return_value = None

        self.pn.notify(self.alert_key, Level.WARNING, self.description, self.html_description)

        self.mock_redis_storage.get_incident_key_for_alert_key.assert_called_once_with(self.alert_key)
        self.mock_pagerduty_client.trigger.assert_called_once_with(
            incident_key=None, description=self.description)
        self.mock_redis_storage.set_incident_key_for_alert_key.assert_called_once_with(
            self.alert_key, self.mock_pagerduty_client.trigger())

    def test_should_not_trigger_with_nominal_level_and_no_key(self):
        self.mock_redis_storage.get_incident_key_for_alert_key.return_value = None

        self.pn.notify(self.alert_key, Level.NOMINAL, self.description, self.html_description)

        self.mock_redis_storage.get_incident_key_for_alert_key.assert_called_once_with(self.alert_key)
        self.assertEqual(self.mock_pagerduty_client.trigger.mock_calls, [])

    def test_should_resolve_with_nominal_level_and_key(self):
        incident_key = 'KEY'
        self.mock_redis_storage.get_incident_key_for_alert_key.return_value = incident_key

        self.pn.notify(self.alert_key, Level.NOMINAL, self.description, self.html_description)

        self.mock_redis_storage.get_incident_key_for_alert_key.assert_called_once_with(self.alert_key)
        self.mock_pagerduty_client.resolve.assert_called_once_with(incident_key=incident_key)
        self.assertEqual(self.mock_pagerduty_client.trigger.mock_calls, [])
        self.mock_redis_storage.remove_incident_for_alert_key.assert_called_once_with(self.alert_key)
