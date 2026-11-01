from unittest import TestCase

from graphitealerts.alerts import Alert
from graphitealerts.level import Level
from graphitealerts.graphite_data_record import NoDataError


def alert_data(rules, **overrides):
    data = {
        'name': 'NAME',
        'target': 'TARGET',
        'rules': rules,
    }
    data.update(overrides)
    return data


class Record:
    target = 'TARGET'

    def __init__(self, value):
        self.value = value

    def get_average(self):
        return self.value

    def get_last_value(self):
        return self.value


class TestDocumentationUrl(TestCase):

    def test_url_without_base_is_none(self):
        alert = Alert(alert_data([]))
        self.assertIsNone(alert.documentation_url())

    def test_url_includes_alert_name(self):
        alert = Alert(alert_data([]), doc_url='https://example.com/docs')
        self.assertEqual(
            alert.documentation_url(), 'https://example.com/docs/NAME')

    def test_url_can_include_target_anchor(self):
        alert = Alert(alert_data([]), doc_url='https://example.com/docs')
        self.assertEqual(
            alert.documentation_url('TARGET'),
            'https://example.com/docs/NAME#TARGET')


class TestAlertRules(TestCase):

    def setUp(self):
        rules = [
            {'greater than 2': 'critical'},
            {'greater than 1': 'warning'},
        ]
        self.alert = Alert(alert_data(rules))

    def test_reads_name_target_and_default_from(self):
        self.assertEqual(self.alert.name, 'NAME')
        self.assertEqual(self.alert.target, 'TARGET')
        self.assertEqual(self.alert.from_, '-1min')

    def test_custom_from_is_preserved(self):
        alert = Alert(alert_data([], **{'from': '-5min'}))
        self.assertEqual(alert.from_, '-5min')

    def test_threshold_rules_are_parsed(self):
        self.assertEqual([rule['val'] for rule in self.alert.parsed_rules], [2.0, 1.0])
        self.assertEqual([rule['action'] for rule in self.alert.parsed_rules],
                         ['critical', 'warning'])

    def test_returns_nominal_when_no_rule_matches(self):
        level, value, rule = self.alert.check_record(Record(0.5))
        self.assertEqual((level, value, rule), (Level.NOMINAL, 0.5, None))

    def test_returns_warning_when_warning_rule_matches(self):
        level, value, rule = self.alert.check_record(Record(1.5))
        self.assertEqual((level, value), (Level.WARNING, 1.5))
        self.assertEqual(rule['action'], 'warning')

    def test_first_matching_rule_wins(self):
        level, value, rule = self.alert.check_record(Record(3))
        self.assertEqual((level, value), (Level.CRITICAL, 3))
        self.assertEqual(rule['action'], 'critical')

    def test_latest_check_method_reads_last_value(self):
        alert = Alert(alert_data(self.alert.rules, check_method='latest'))
        level, value, rule = alert.check_record(Record(3))
        self.assertEqual((level, value), (Level.CRITICAL, 3))
        self.assertEqual(rule['action'], 'critical')


class TestAlertLessThanRules(TestCase):

    def setUp(self):
        rules = [
            {'less than 1': 'critical'},
            {'less than 2': 'warning'},
        ]
        self.alert = Alert(alert_data(rules))

    def test_critical_rule_matches_below_critical_limit(self):
        self.assertEqual(self.alert.check_record(Record(0))[0], Level.CRITICAL)

    def test_warning_rule_matches_between_limits(self):
        self.assertEqual(self.alert.check_record(Record(1.5))[0], Level.WARNING)

    def test_no_rule_matches_above_limits(self):
        self.assertEqual(self.alert.check_record(Record(3))[0], Level.NOMINAL)


class TestAlertNoDataAndExclusions(TestCase):

    def setUp(self):
        self.alert = Alert(alert_data(
            [{'greater than 1': 'warning'}], exclude=['excluded']))

    def test_no_data_returns_no_data_level(self):
        class EmptyRecord(Record):
            def get_average(self):
                raise NoDataError()

        level, value, rule = self.alert.check_record(EmptyRecord(0))
        self.assertEqual(level, 'NO DATA')
        self.assertEqual(value, 'No data')
        self.assertEqual(rule['description'], 'No data for alert')

    def test_excluded_target_returns_nominal(self):
        record = Record(10)
        record.target = 'excluded'
        self.assertEqual(
            self.alert.check_record(record), (Level.NOMINAL, 'Excluded', None))


class TestAlertWithoutRules(TestCase):

    def test_alert_always_returns_nominal(self):
        alert = Alert(alert_data([]))
        self.assertEqual(alert.check_record(Record(2)), (Level.NOMINAL, 2, None))
