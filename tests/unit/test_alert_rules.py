import random
import unittest
from graphitealerts.alerts import AlertRules, Rule
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
            r = Rule(*list(rule.items()[0]))
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
            r = Rule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            self.assertEqual('slack', r.notifiers[0][0])

        # now something more complex
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify by slack,twilio
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = Rule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            self.assertEqual('slack', r.notifiers[0][0])
            self.assertEqual('twilio', r.notifiers[1][0])

        # now something more complex
        yml = """
rules:
    - less than 0.5:
        - critical
        - notify admin by slack,twilio
        """
        settings = yaml.load(yml)
        for rule in settings['rules']:
            r = Rule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            self.assertEqual('slack', r.notifiers[0][0])
            self.assertEqual('twilio', r.notifiers[1][0])
            self.assertEqual('admin', r.notifiers[0][1])
            self.assertEqual('admin', r.notifiers[1][1])

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
            r = Rule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            self.assertEqual('slack', r.notifiers[0][0])
            self.assertEqual('twilio_sms', r.notifiers[1][0])
            self.assertEqual('admin', r.notifiers[0][1])
            self.assertEqual('user_1', r.notifiers[1][1])

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
            r = Rule(*list(rule.items()[0]))
            self.assertEqual(r.level, 'CRITICAL')
            self.assertEqual('slack', r.notifiers[0][0])
            self.assertEqual('twilio_sms', r.notifiers[1][0])
            self.assertEqual('admin', r.notifiers[0][1])
            self.assertEqual('user_1', r.notifiers[1][1])


if __name__ == '__main__':
    unittest.main()
