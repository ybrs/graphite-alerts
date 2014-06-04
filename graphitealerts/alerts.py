import operator
import logging

from graphite_data_record import NoDataError
from level import Level

log = logging.getLogger('alerts')

levels = (Level.WARNING.upper(), Level.CRITICAL.upper(), Level.NOMINAL.upper())

class Rule(object):
    def __init__(self, k, v):

        # there are only 2 cases, so we dont care about a tokenizer
        if 'greater than' in k:
            self._val = float(k.split('greater than')[1])
            self._op = operator.gt
        elif 'less than' in k:
            self._op = operator.lt
            self._val = float(k.split('less than')[1])
        self.rule = k
        self.action = v

        self.notifiers = []
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
            notify admin by slack, twilio_sms, twilio_call
        >>> r = Rule('greater than 5', 'critical')
        >>> r.parse_notify_line('notify by slack')
        [('slack', 'all')]

        >>> r = Rule('greater than 5', 'critical')
        >>> r.parse_notify_line('notify by slack, twilio')
        [('slack', 'all'), ('twilio', 'all')]

        >>> r = Rule('greater than 5', 'critical')
        >>> r.parse_notify_line('notify admin by slack, twilio')
        [('slack', 'admin'), ('twilio', 'admin')]

        >>> r = Rule('greater than 5', 'critical')
        >>> r.parse_notify_line('notify admin by slack, twilio after 10 minutes')
        [('slack', 'admin'), ('twilio', 'admin')]

        """
        import re

        token_specs = [
            ('keyword_notify', 'notify'),
            ('keyword_by', 'by'),
            ('keyword_after', 'after'),
            ('others', '\w+')
        ]

        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specs)
        get_token = re.compile(tok_regex).search
        mo = get_token(s)
        print ">>>", s
        while mo is not None:
            print ">>> ", mo.groupdict()
            pos = mo.end()
            mo = get_token(s, pos)


        # matches = re.search('notify(?P<contacts>([a-zA-Z ,]+)?)by(?P<notifier>([a-zA-Z ,]+)?)(?P<afterkw>after)(?P<after>.*)', s).groupdict()
        # print matches
        # notifiers = matches['notifier'].strip().split(',')
        # notify_contacts = matches['contacts'].strip().split(',')
        #
        # self.after = matches['after']
        #
        # for notifier in notifiers:
        #     notifier = notifier.strip()
        #     for notify_contact in notify_contacts:
        #         notify_contact = notify_contact.strip()
        #         if not notify_contact:
        #             notify_contact = 'all'
        #         self.notifiers.append((notifier, notify_contact))
        #
        # return self.notifiers

    def match(self, val):
        """
        returns distance or false
        """
        if self._op(val, self._val):
            return abs(self._val - val)

    def __repr__(self):
        return "<Rule (%s - %s)>" % (self.rule, self.action)

class AlertRules(object):
    def __init__(self):
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
        rule = Rule(k, v)
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
        return best_match[1]


class Alert(object):

    def __init__(self, alert_data, doc_url=None):
        log.debug(alert_data)

        self.name = alert_data['name']
        self.target = alert_data['target']        

        self.rules = alert_data.get('rules', {})
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
        """ i know this is the worst parser of all times """        
        self.parsed_rules = []
        for r in self.rules:
            for rule, action in r.iteritems():
                if 'greater' in rule:
                    val = rule.split('greater than')[1]
                    op = operator.gt                                    
                elif 'less' in rule:
                    val = rule.split('less than')[1]
                    op = operator.lt
                    
                if 'historical' in val:
                    val = val
                else:
                    val = float(val)
                print "---------------------"
                print action
                print "---------------------"
                if isinstance(action, str):
                    self.parsed_rules.append({'op': op, 'val': val, 'action': action, 'description': rule})
                else:
                    # if isinstance(action, list):
                    raise Exception('not yet ready')
        raise Exception(self.parsed_rules)

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

    def check_record(self, record, history_records=None):
        if record.target in self.exclude:
            return Level.NOMINAL, 'Excluded'
        try:            
            if self.check_method == 'latest':
                value = record.get_last_value()
            elif self.check_method == 'average':
                value = record.get_average()
            elif self.check_method == 'historical':
                # this check is different from others,
                # it will try to find nominal value by looking at old data
                # then check if its over it
                # makes very easy to add alerts on arbitary data
                myhistory = self.find_record_in_history(record, history_records)
                historical_val = myhistory.get_average()
                value = record.get_average()
                log.debug('historical: %s', historical_val)
                log.debug('now: %s', value)
            else:
                raise Exception('unknown check method')                        
        except NoDataError:
            return 'NO DATA', 'No data', {'description': 'No data for alert'}
        
        for rule in self.parsed_rules:
            
            try:
                if 'historical' in rule['val']:
                    rule_val = eval(rule['val'].replace('historical', historical_val))
                    log.debug('Historical rule set up with %s', rule_val)
            except:
                rule_val = rule['val']
            
            if rule['op'](value, rule_val):
                if rule['action'] == 'warning':
                    return Level.WARNING, value, rule
                elif rule['action'] == 'critical':
                    return Level.CRITICAL, value, rule
                elif rule['action'] == 'nothing':
                    return Level.NOMINAL, value, rule
        return Level.NOMINAL, value, None
        



if __name__ == '__main__':
    get_alerts()
