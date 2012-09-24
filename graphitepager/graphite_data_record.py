"""Data record for a single metric of Graphite data"""


class GraphiteDataRecord(object):

    def __init__(self, metric_string):
        meta, data = metric_string.split('|')
        self.target, start_time, end_time, step = meta.split(',')
        self.start_time = int(start_time)
        self.end_time = int(end_time)
        self.step = int(step)

        self.values = [float(value) for value in data.split(',')]

    @property
    def avg(self):
        return sum(self.values) / len(self.values)
