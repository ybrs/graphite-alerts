import random
import unittest
from graphitealerts.alerts import AlertRules, Rule
import yaml
from graphitealerts.rule_parser import parse, parser, lexer

class TestRuleParser(unittest.TestCase):

    def test_basic_matches(self):

        class obj:
            def __init__(self):
                self.time_defs = []
                self.after = False
                self.calc_seconds = 0
                self.notify_contacts = []
                self.notify_by = []

            def after_time(self):
                self.calc_seconds = 0
                for time_def in self.time_defs:
                    self.calc_seconds += time_def.seconds
                return self.calc_seconds

        o = obj()
        parse(o, 'after 2 hours and 10 minutes and 5 seconds')
        seconds = (2 * 60 * 60) + (10 * 60) + 5
        assert seconds == o.after_time()

        o = obj()
        parse(o, 'notify admin and user1 user2')
        assert 'admin' in o.notify_contacts and 'user1' in o.notify_contacts and 'user2' in o.notify_contacts

        o = obj()
        parse(o, 'by twilio')
        assert 'twilio' in o.notify_by

        o = obj()
        parse(o, 'by twilio and foo')
        assert 'twilio' in o.notify_by and 'foo' in o.notify_by

        o = obj()
        parse(o, 'notify admin user1 user2 after 10 seconds')
        self.assertEqual(o.after_time(), 10)
        assert 'admin' in o.notify_contacts and 'user1' in o.notify_contacts and 'user2' in o.notify_contacts

        o = obj()
        parse(o, 'notify admin, foo by twilio and phone after 10 minutes')
        assert 'admin' in o.notify_contacts and 'foo' in o.notify_contacts
        assert 'twilio' in o.notify_by and 'phone' in o.notify_by



if __name__ == '__main__':
    unittest.main()
