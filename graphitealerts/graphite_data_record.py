'''
Data record for a single metric of Graphite data
'''

import re
import logging

log = logging.getLogger('graphite_data_record')

class NoDataError(ValueError):
    pass

class GraphiteDataRecord(object):

    def __init__(self, metric_string, historical=False):
        meta, data = metric_string.split('|')
        self.target, start_time, end_time, step = meta.rsplit(',', 3)
        
        log.debug('metric_string %s', metric_string)
            
        if historical:    
            r = re.match('summarize\((.*), ".*", ".*"\)', self.target)
            if r:
                self.org_target = self.target
                self.target = r.groups()[0]            
                log.debug('historical groups %s', r.groups())
                            
        self.start_time = int(start_time)
        self.end_time = int(end_time)
        self.step = int(step)

        self.values = [_float_or_none(value) for value in data.rsplit(',')]

    def get_average(self):
        values = [value for value in self.values if value is not None]
        log.debug('average values %s', values)
        if len(values) == 0:
            raise NoDataError()
        return sum(values) / len(values)

    def get_last_value(self):
        log.debug('last value %s', list(reversed(self.values)))
        for value in reversed(self.values):
            if value is not None:
                return value
        raise NoDataError()

    def __repr__(self):
        return '<GraphiteDataRecord (target:%s values:%s)>' % (self.target, self.values)

def _float_or_none(value):
    try:
        return float(value)
    except ValueError:
        return None