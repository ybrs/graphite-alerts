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
            self.assertIn('slack', r.notifiers[0][0])

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
            self.assertIn('slack', r.notifiers[0][0])
            self.assertIn('twilio', r.notifiers[1][0])

if __name__ == '__main__':
    unittest.main()
