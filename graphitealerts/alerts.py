import operator
import logging

from graphite_data_record import NoDataError
from level import Level

log = logging.getLogger('alerts')

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
        self.min_threshold = alert_data.get('min_threshold', 0)        
        self.notifiers += ['console']
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
                self.parsed_rules.append({'op': op, 'val': val, 'action': action, 'description': rule})

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
