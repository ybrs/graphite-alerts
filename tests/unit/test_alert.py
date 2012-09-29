from unittest import TestCase

from mock import call, MagicMock
import requests

from graphitepager.alerts import Alert

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

class TestAlertIncreasing(TestCase):

    def setUp(self):
        self.alert = Alert(ALERT_INC)

    def test_name_matches(self):
        self.assertEqual(self.alert.name, ALERT_INC['name'])

    def test_target_matches(self):
        self.assertEqual(self.alert.target, ALERT_INC['target'])

    def test_warning_matches(self):
        self.assertEqual(self.alert.warning, ALERT_INC['warning'])

    def test_critical_matches(self):
        self.assertEqual(self.alert.critical, ALERT_INC['critical'])

    def test_should_return_none_for_low_value(self):
        self.assertEqual(self.alert.check_value(0), None)

    def test_should_return_warning_for_warning_value(self):
        self.assertEqual(self.alert.check_value(self.alert.warning), 'WARNING')

    def test_should_return_warning_for_mid_value(self):
        self.assertEqual(self.alert.check_value(1.5), 'WARNING')

    def test_should_return_critical_for_critical_value(self):
        self.assertEqual(self.alert.check_value(2), 'CRITICAL')

    def test_should_return_critical_for_high_value(self):
        self.assertEqual(self.alert.check_value(3), 'CRITICAL')


class TestAlertDescreasing(TestCase):

    def setUp(self):
        self.alert = Alert(ALERT_DEC)

    def test_name_matches(self):
        self.assertEqual(self.alert.name, ALERT_DEC['name'])

    def test_target_matches(self):
        self.assertEqual(self.alert.target, ALERT_DEC['target'])

    def test_warning_matches(self):
        self.assertEqual(self.alert.warning, ALERT_DEC['warning'])

    def test_critical_matches(self):
        self.assertEqual(self.alert.critical, ALERT_DEC['critical'])

    def test_should_return_critical_for_low_value(self):
        self.assertEqual(self.alert.check_value(0), 'CRITICAL')

    def test_should_return_critical_for_critical_value(self):
        self.assertEqual(self.alert.check_value(self.alert.critical), 'CRITICAL')

    def test_should_return_warning_for_mid_value(self):
        self.assertEqual(self.alert.check_value(1.5), 'WARNING')

    def test_should_return_warning_for_warning_value(self):
        self.assertEqual(self.alert.check_value(self.alert.warning), 'WARNING')

    def test_should_return_none_for_high_value(self):
        self.assertEqual(self.alert.check_value(3), None)
