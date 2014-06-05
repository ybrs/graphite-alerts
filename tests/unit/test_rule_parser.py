import random
import unittest
from graphitealerts.alerts import AlertRules, Rule, NotifyRule, NotifyRules
import yaml
from graphitealerts.rule_parser import parse, parser, lexer

class TestRuleParser(unittest.TestCase):

    def test_rules(self):

        def gen_rule(rule_id, s):
            o = NotifyRule()
            o.rule_id = rule_id
            parse(o, s)
            return o

        container = NotifyRules()
        container.add(gen_rule(1, 'after 10 minutes'))

        rule = container.best_match(700)
        assert rule.rule_id == 1

        container.add(gen_rule(2, 'after 20 minutes'))
        rule = container.best_match(700)
        assert rule.rule_id == 1

        rule = container.best_match(25 * 60)
        assert rule.rule_id == 2

        container.add(gen_rule(2, 'after 0 minutes'))
        rule = container.best_match(25 * 60)
        assert rule.rule_id == 2
        rule = container.best_match(5 * 60)
        assert rule.rule_id == 2


    def test_basic_matches(self):

        o = NotifyRule()
        parse(o, 'after 2 hours and 10 minutes and 5 seconds')
        seconds = (2 * 60 * 60) + (10 * 60) + 5
        assert seconds == o.after_time

        o = NotifyRule()
        parse(o, 'notify admin and user1 user2')
        assert 'admin' in o.notify_contacts and 'user1' in o.notify_contacts and 'user2' in o.notify_contacts

        o = NotifyRule()
        parse(o, 'by twilio')
        assert 'twilio' in o.notify_by

        o = NotifyRule()
        parse(o, 'by twilio and foo')
        assert 'twilio' in o.notify_by and 'foo' in o.notify_by

        o = NotifyRule()
        parse(o, 'notify admin user1 user2 after 10 seconds')
        self.assertEqual(o.after_time, 10)
        assert 'admin' in o.notify_contacts and 'user1' in o.notify_contacts and 'user2' in o.notify_contacts

        o = NotifyRule()
        parse(o, 'notify admin, foo by twilio and phone after 10 minutes')
        assert 'admin' in o.notify_contacts and 'foo' in o.notify_contacts
        assert 'twilio' in o.notify_by and 'phone' in o.notify_by

        o = NotifyRule()
        parse(o, 'notify by twilio')
        assert o.notify_contacts == []


if __name__ == '__main__':
    unittest.main()
