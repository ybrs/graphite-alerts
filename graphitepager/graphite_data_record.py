"""Data record for a single metric of Graphite data"""


class GraphiteDataRecord(object):

    def __init__(self, metric_string):
        meta, data = metric_string.split('|')
        self.target, start_time, end_time, step = meta.split(',')
        self.start_time = int(start_time)
        self.end_time = int(end_time)
        self.step = int(step)

        self.values = [_float_or_none(value) for value in data.split(',')]

    @property
    def avg(self):
        values = [value for value in self.values if value is not None]
        return sum(values) / len(self.values)

def _float_or_none(value):
    try:
        return float(value)
    except ValueError:
        return None
