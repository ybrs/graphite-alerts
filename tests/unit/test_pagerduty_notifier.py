from unittest import TestCase

from mock import patch, MagicMock

from graphitepager.pagerduty_notifier import PagerdutyNotifier
from graphitepager.redis_storage import RedisStorage


class _BaseTest(TestCase):

    def setUp(self):
        self.pd_key = 'PAGERDUTY KEY'
        self.storage = MagicMock(RedisStorage)

        with patch('graphitepager.pagerduty_notifier.PagerDuty') as mock_pd:
            self.pdn = PagerdutyNotifier(self.pd_key, self.storage)
            self.mock_pd_client = mock_pd

        self.value = 0
        self.alert = 'ALERT'
        self.target = 'TARGET'

    def test_creates_pagerduty_client(self):
        self.mock_pd_client.assert_called_once_with(self.pd_key)

    def test_gets_key_for_incident(self):
        self.storage.get_incident_key_for_alert_and_record.assert_called_once_with(self.alert, self.target)


class TestPagerDutyNotifierNominal(_BaseTest):

    def setUp(self):
        super(TestPagerDutyNotifierNominal, self).setUp()
        self.pdn.nominal(self.alert, self.target, self.value)

    def test_removes_incident_key(self):
        self.storage.remove_incident_for_alert_and_record.assert_called_once_with( self.alert, self.target)

    def test_resolves_incident_key(self):
        self.mock_pd_client().resolve.assert_called_once_with(incident_key=self.storage.get_incident_key_for_alert_and_record())


class TestPagerDutyNotifierNominalWithNoKey(_BaseTest):

    def setUp(self):
        super(TestPagerDutyNotifierNominalWithNoKey, self).setUp()
        self.storage.get_incident_key_for_alert_and_record.return_value = None
        self.pdn.nominal(self.alert, self.target, self.value)

    def test_does_not_try_resolve_incide_key(self):
        self.assertEqual(len(self.storage.remove_incident_for_alert_and_record.mock_calls), 0)

    def test_does_not_try_resolve_incident(self):
        self.assertEqual(len(self.mock_pd_client().resolve.mock_calls), 0)


class TestPagerDutyNotifierWarning(_BaseTest):

    def setUp(self):
        super(TestPagerDutyNotifierWarning, self).setUp()
        self.pdn.warning(self.alert, self.target, self.value)

    def test_opens_incident_key(self):
        self.mock_pd_client().trigger.assert_called_once_with(incident_key=self.storage.get_incident_key_for_alert_and_record())


class TestPagerDutyNotifierCritical(_BaseTest):

    def setUp(self):
        super(TestPagerDutyNotifierCritical, self).setUp()
        self.pdn.critical(self.alert, self.target, self.value)

    def test_opens_incident_key(self):
        self.mock_pd_client().trigger.assert_called_once_with(incident_key=self.storage.get_incident_key_for_alert_and_record())
