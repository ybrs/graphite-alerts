from unittest import TestCase

from mock import call, MagicMock
import requests

from graphitepager.alerts import Alert
from graphitepager.graphite_data_record import NoDataError
from graphitepager.pagerduty_notifier import PagerdutyNotifier

ALERT_INC = {
    'target': 'TARGET',
    'warning': 1,
    'critical': 2,
    'name': 'NAME',
}
ALERT_DEC = {
    'target': 'TARGET',
    'warning': 2,
    'critical': 1,
    'name': 'NAME',
}

class _BaseTestCase(TestCase):

    def _check_value(self, value):
        self.alert.check_value_from_callable(lambda: value)

    def assert_notified_as_nominal(self, value):
        self.notifier.nominal.assert_called_once_with(
            self.alert.name,
            self.alert.target,
            value
        )

    def assert_notified_as_warning(self, value):
        self.notifier.warning.assert_called_once_with(
            self.alert.name,
            self.alert.target,
            value
        )

    def assert_notified_as_critical(self, value):
        self.notifier.critical.assert_called_once_with(
            self.alert.name,
            self.alert.target,
            value
        )


class TestAlertIncreasing(_BaseTestCase):

    def setUp(self):
        self.alert = Alert(ALERT_INC)
        self.notifier = MagicMock(PagerdutyNotifier)
        self.alert.add_notifier(self.notifier)

    def test_name_matches(self):
        self.assertEqual(self.alert.name, ALERT_INC['name'])

    def test_target_matches(self):
        self.assertEqual(self.alert.target, ALERT_INC['target'])

    def test_warning_matches(self):
        self.assertEqual(self.alert.warning, ALERT_INC['warning'])

    def test_critical_matches(self):
        self.assertEqual(self.alert.critical, ALERT_INC['critical'])

    def test_should_notify_nominal_for_low_value(self):
        self._check_value(0)
        self.assert_notified_as_nominal(0)

    def test_should_notify_warning_for_warning_value(self):
        self._check_value(self.alert.warning)
        self.assert_notified_as_warning(self.alert.warning)

    def test_should_notify_warning_for_mid_value(self):
        self._check_value(1.5)
        self.assert_notified_as_warning(1.5)

    def test_should_notify_critical_for_critical_value(self):
        self._check_value(2)
        self.assert_notified_as_critical(2)

    def test_should_notify_critical_for_high_value(self):
        self._check_value(3)
        self.assert_notified_as_critical(3)


class TestAlertDescreasing(_BaseTestCase):

    def setUp(self):
        self.alert = Alert(ALERT_DEC)
        self.notifier = MagicMock(PagerdutyNotifier)()
        self.alert.add_notifier(self.notifier)

    def test_name_matches(self):
        self.assertEqual(self.alert.name, ALERT_DEC['name'])

    def test_target_matches(self):
        self.assertEqual(self.alert.target, ALERT_DEC['target'])

    def test_warning_matches(self):
        self.assertEqual(self.alert.warning, ALERT_DEC['warning'])

    def test_critical_matches(self):
        self.assertEqual(self.alert.critical, ALERT_DEC['critical'])

    def test_should_notify_critical_for_low_value(self):
        self._check_value(0)
        self.assert_notified_as_critical(0)

    def test_should_notify_critical_for_critical_value(self):
        self._check_value(self.alert.critical)
        self.assert_notified_as_critical(self.alert.critical)

    def test_should_notify_warning_for_mid_value(self):
        self._check_value(1.5)
        self.assert_notified_as_warning(1.5)

    def test_should_notify_warning_for_warning_value(self):
        self._check_value(self.alert.warning)
        self.assert_notified_as_warning(self.alert.warning)

    def test_should_notify_none_for_high_value(self):
        self._check_value(3)
        self.assert_notified_as_nominal(3)


class TestAlertHasNoData(_BaseTestCase):

    def setUp(self):
        self.alert = Alert(ALERT_DEC)

    def test_should_return_no_data_for_no_data(self):
        def raiser():
            raise NoDataError()

        returned = self.alert.check_value_from_callable(raiser)
        self.assertEqual(returned, 'NO DATA')
