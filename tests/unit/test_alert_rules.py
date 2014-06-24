import random
import unittest
from graphitealerts.alerts import AlertRules, AlertRule, Alert
import yaml

class TestRules(unittest.TestCase):

    def test_basic_matches(self):
        alert_rules = AlertRules()
        alert_rules.add('less than 6', '')
        alert_rules.add('greater than 6', '')
        alert_rules.add('greater than 2', '')
        alert_rules.add('greater than 3', '')

        rule = alert_rules.match(4)
        self.assertEqual(rule._val, 3.0)

        rule = alert_rules.match(5)
        self.assertEqual(rule._val, 6.0)

        rule = alert_rules.match(7)
        self.assertEqual(rule._val, 6.0)

        rule = alert_rules.match(1)
        self.assertEqual(rule._val, 6.0)

    def test_actions(self):
        yml = """
rules:
    - less than 0.5:
        critical
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = AlertRule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'critical')

        # now something more complex
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify by slack
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = AlertRule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            notifiers = r.notify_rules.matches(10)
            assert notifiers
            assert 'slack' in notifiers[0].notify_by


        # now something more complex
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify by slack,twilio
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = AlertRule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            notifier = r.notify_rules.matches(10)[0]
            assert 'slack' in notifier.notify_by and 'twilio' in notifier.notify_by



        # now something with contacts complex
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify admin by slack,twilio
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = AlertRule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            notifier = r.notify_rules.matches(10)[0]
            assert 'slack' in notifier.notify_by and 'twilio' in notifier.notify_by
            assert 'admin' in notifier.notify_contacts

        # now something with more users
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify admin by slack
        - notify user_1 by twilio_sms
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = AlertRule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            notifiers = r.notify_rules.matches(10)
            assert len(notifiers) == 2
            assert notifiers[0].notify_contacts == ['admin']
            assert notifiers[1].notify_contacts == ['user_1']

        # now something with times
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify user_1 by slack after 5 minutes
        - notify admin by twilio_sms after 10 minutes
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = AlertRule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            notifiers = r.notify_rules.matches(5 * 60)
            assert len(notifiers) == 1
            assert notifiers[0].notify_contacts == ['user_1']
            notifiers = r.notify_rules.matches(10 * 60)
            assert notifiers[0].notify_contacts == ['user_1']
            assert notifiers[1].notify_contacts == ['admin']

    def test_alert_target(self):
        # starting with something easy
        yml = """
        - target: summarize(servers.*.*.diskspace.*.inodes_percentfree, "1min", "avg")
          name: diskspace
          from: -10min
          check_method: average
          rules:
            - less than 10:
                warning
            - less than 5:
                critical
        """
        alert_data = yaml.load(yml)
        alert = Alert(alert_data[0])
        assert alert.name == 'diskspace'
        rule = alert.alert_rules.match(4)
        assert rule._val == 5.0
        rule = alert.alert_rules.match(6)
        assert rule._val == 10.0

        # something a bit complicated
        yml = """
        - target: summarize(servers.*.*.diskspace.*.inodes_percentfree, "1min", "avg")
          name: diskspace
          from: -10min
          check_method: average
          rules:
            - less than 10:
                - warning
                - notify user by twilio
            - less than 5:
                critical
        """
        alert_data = yaml.load(yml)
        alert = Alert(alert_data[0])
        assert alert.name == 'diskspace'
        rule = alert.alert_rules.match(4)
        assert rule._val == 5.0
        notify_rules = rule.notify_rules.matches(1)
        assert notify_rules == []

        rule = alert.alert_rules.match(6)
        assert rule._val == 10.0
        assert rule.level.lower() == 'warning'
        notify_rules = rule.notify_rules.matches(10)
        assert 'twilio' in notify_rules[0].notify_by
        assert 'user' in notify_rules[0].notify_contacts

        # something a bit more complicated
        yml = """
        - target: summarize(servers.*.*.diskspace.*.inodes_percentfree, "1min", "avg")
          name: diskspace
          from: -10min
          check_method: average
          rules:
            - less than 10:
                - warning
                - notify user by twilio after 10 minutes
            - less than 5:
                critical
        """
        alert_data = yaml.load(yml)
        alert = Alert(alert_data[0])
        assert alert.name == 'diskspace'
        rule = alert.alert_rules.match(4)
        assert rule._val == 5.0
        notify_rules = rule.notify_rules.matches(1)
        assert notify_rules == []

        rule = alert.alert_rules.match(6)
        assert rule._val == 10.0
        assert rule.level.lower() == 'warning'
        notify_rules = rule.notify_rules.matches(10)
        print "notify rules", notify_rules

if __name__ == '__main__':
    unittest.main()
