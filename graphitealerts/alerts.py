import operator
import logging

from graphite_data_record import NoDataError
from level import Level
import time

log = logging.getLogger('alerts')

levels = (Level.WARNING.upper(), Level.CRITICAL.upper(), Level.NOMINAL.upper())

class NotifyRule(object):
    """
    used for notification lines
    """
    def __init__(self):
        self.time_defs = []
        self.after = False
        self.calc_seconds = 0
        self.notify_contacts = []
        self.notify_by = []

    @property
    def after_time(self):
        self.calc_seconds = 0
        for time_def in self.time_defs:
            self.calc_seconds += time_def.seconds
        return self.calc_seconds

    def __repr__(self):
        return '<NotifyRule after:%s seconds, notify_by:%s, contacts:%s>' % (self.after_time, self.notify_by, self.notify_contacts)

class NotifyRules(object):

    def __init__(self):
        self.notify_rules = []

    def add(self, rule):
        self.notify_rules.append(rule)

    def matches(self, after_seconds):
        """
            returns all matching rule after X seconds, because if each rule matches,
            we want to notify all - if its notified already for this rule, we dont notify again,
            so no harm returning all.

            rule.after_time = 0
            rule.after_time = 100
            rule.after_time = 200

            best_match for 300 => 200
            best_match for 150 => 100

        """
        matches = []
        for rule in self.notify_rules:
            distance = after_seconds - rule.after_time
            if distance >= 0:
                matches.append(rule)
        return matches

    def __repr__(self):
        return '<NotifyRules [%s]>' % self.notify_rules


class AlertRule(object):

    def __init__(self, app, k, v):
        self.app = app
        # there are only 2 cases, so we dont care about a tokenizer
        if 'greater than' in k:
            self._val = float(k.split('greater than')[1])
            self._op = operator.gt
        elif 'less than' in k:
            self._op = operator.lt
            self._val = float(k.split('less than')[1])
        elif 'lost metric' in k:
            self._op = 'lost_metric'

        self.rule = k
        self.action = v

        self.notifiers = []
        self.notify_rules = NotifyRules()
        self.after = None

        if isinstance(self.action, str):
            self.level = self.action
        elif isinstance(self.action, list):
            for line in self.action:
                if line.upper() in levels:
                    self.level = line.upper()
                elif 'notify' in line.lower():
                    self.parse_notify_line(line)

    def parse_notify_line(self, s):
        """
        notifier line can be:

            notify by slack
            notify by slack, twilio_sms

        or you can notify some of the contacts

            notify admin by slack, twilio_sms, twilio_call

        or call some of the contacts after 10 minutes

            notify admin by twilio_sms after 10 minutes
            notify admin by twilio_call after 20 minutes

        """
        from rule_parser import parse
        rule = NotifyRule()
        parse(rule, s)
        self.notify_rules.add(rule)

    def match(self, val):
        """
        returns distance or false
        """
        print "Self op", self._op
        if self._op == 'lost_metric':
            if val == 'lost_metric':
                return 1
        else:
            if self._op(val, self._val):
                try:
                    return abs(self._val - val)
                except:
                    # TODO: not so sure about this...
                    pass

    def __repr__(self):
        return "<Rule (%s - %s)>" % (self.rule, self.action)

class AlertRules(object):
    def __init__(self, app):
        self.app = app
        self._rules = []

    def add(self, k, v):
        """
        rules come in arbitrary order
            greater than 2: .....
            greater than 1: .....
            greater than 0.1: ....
        when we try to match, we match with only one rule:
        say for value 5 we need to match
            greater than 2: .....
        rule not all of them.

        rules might have intersections
            less than 4: ....
            greater than 2: .....
        in this case we choose the closest match rule.

        value is 5 =>
            greater than 2  => 2+  -> diff: 3
            greater than 3  => 3+  -> diff: 2
            less than 6     => 6-  -> diff: 1
            ----> less than 6 wins
        """
        rule = AlertRule(self.app, k, v)
        self._rules.append(rule)
        return rule

    def match(self, v):
        best_match = None
        for rule in self._rules:
            distance = rule.match(v)
            if distance:
                if not best_match:
                    best_match = (distance, rule)
                if distance < best_match[0]:
                    best_match = (distance, rule)
        if best_match:
            return best_match[1]
        return best_match


class Alert(object):
    """
    An alert can have rules, a rule has limits/bounds (eg. greater than 1)
    and a rule might have different notify rules.

    so its like,
        Alert (target) >
            AlertRules (container for alertrule[s] finds best match etc.) ->
                AlertRule (greater than...) >
                    NotifyRules (container for NotifyRule[s] finds best match etc.)->
                        Notify Rule (call ...)

    eg:

    - target: summarize(http_check.*.*,"1min","avg")
      name: http checks
      rules:
        - greater than 1:
            - warning
            - notify by slack and hipchat
        - greater than 2:
            - critical
            - notify by slack                           # notifies everyone
            - notify by twilio_sms after 5 minutes      # sms to admin after 5 minutes, if we still have the problem
            - notify by twilio_call after 10 minutes    # call admin after 10 minutes if we still have the issue

    """

    def __init__(self, app, alert_data, doc_url=None):
        log.debug(alert_data)

        self.app = app
        self.name = alert_data['name']
        self.target = alert_data['target']        

        self.rules_data = alert_data.get('rules', {})
        self.alert_rules = AlertRules(self.app)
        self.parse_rules()
        
        self.from_ = alert_data.get('from', '-1min')
        self.exclude = set(alert_data.get('exclude', []))
        self.check_method = alert_data.get('check_method', 'average')
        self.notifiers = alert_data.get('notifiers', [])
        self.notifiers += ['console']
        self.min_threshold = alert_data.get('min_threshold', 0)
        self.historical = alert_data.get('historical', 'summarize(target, 1hour, avg) from -2days')
        self.smart_average_from = alert_data.get('smart_average_from', '-1days')
        self._doc_url = doc_url

    def parse_rules(self):  
        """ parses the rule lines """
        for r in self.rules_data:
            print "!!!!", r
            for k, v in r.iteritems():
                self.alert_rules.add(k, v)

    def documentation_url(self, target=None):
        if self._doc_url is None:
            return None
        template = self._doc_url + '/' + self.name
        if target is None:
            url = template
        else:
            url = template + '#' + target
        return url

    def find_record_in_history(self, record, history):
        for i in history:
            log.debug('find %s in %s', i.target, record.target)
            if i.target == record.target:
                return i

    def check_record(self, app, record, history_records=None):
        print ">>>> checking record >>>", record

        for val in record.values:
            if val is None: # we skip None values, since we really dont know what to do with them
                continue
            print ">>>", val
            rule = self.alert_rules.match(val)
            if rule:
                print rule.notify_rules, rule.level
                # we have to find the best notifier for this alert.
                first_seen = app.storage.get_first_seen(record.target)
                if not first_seen:
                    app.storage.set_first_seen(record.target)
                    time_passed = 0
                else:
                    time_passed = int(time.time() - first_seen)
                print "time_passed:", time_passed
                notifiers = rule.notify_rules.matches(time_passed)
                logging.debug("found notifiers [%s]", notifiers)
                for notifier in notifiers:
                    for notify_by in notifier.notify_by:
                        n = app.notifiers.get(notify_by, None)
                        if not n:
                            # notifier might be disabled, dont panic
                            continue
                        print ">>>> notifier (n)", n, record.target, rule
                        n.notify(record.target, rule, val)