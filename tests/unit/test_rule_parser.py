import random
import unittest
from graphitealerts.alerts import AlertRules, Rule
import yaml
from graphitealerts.rule_parser import parse, parser, lexer

class TestRuleParser(unittest.TestCase):

    def test_basic_matches(self):
        # parser.parse(lexer.lex('notify admin foo by twilio mail after 10 minutes'))
        # parser.parse(lexer.lex('after 10 minutes'))
        # parser.parse(lexer.lex('notify admin'))
        # parser.parse(lexer.lex('notify admin foo by twilio mail after 10 minutes'))
        # parser.parse(lexer.lex('notify admin, foo by twilio phone after 10 minutes'))
        # parser.parse(lexer.lex('notify admin, foo by twilio and phone after 10 minutes'))
        class obj:
            def __init__(self):
                self.time_defs = []
                self.after = False
                self.calc_seconds = 0
                self.notify_contacts = []

            def after_time(self):
                self.calc_seconds = 0
                for time_def in self.time_defs:
                    self.calc_seconds += time_def.seconds
                return self.calc_seconds

        # o = obj()
        # parse(o, 'after 2 hours and 10 minutes and 5 seconds')
        # seconds = (2 * 60 * 60) + (10 * 60) + 5
        # assert seconds == o.after_time()

        o = obj()
        parse(o, 'notify admin and user1 user2')# by twilio_sms after 10 minutes')
        # assert o.calc_seconds == 600
        # assert 'admin' in o.notify_contacts and 'user1' in o.notify_contacts


        # parse(obj, 'notify admin, foo by twilio and phone after 10 minutes')

if __name__ == '__main__':
    unittest.main()
