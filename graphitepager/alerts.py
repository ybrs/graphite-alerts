import operator

from yaml import load, dump
from graphite_data_record import NoDataError
from level import Level


class Alert(object):

    def __init__(self, alert_data):
        print alert_data
        self.name = alert_data['name']
        self.target = alert_data['target']
        self.warning = alert_data['warning']
        self.critical = alert_data['critical']
        self.from_ = alert_data.get('from', '-1min')
        self.exclude = set(alert_data.get('exclude', []))

        self.comparison_operator = self._determine_comparison_operator(self.warning, self.critical)

    def _determine_comparison_operator(self, warn_value, crit_value):
        if warn_value > crit_value:
            return operator.le
        elif crit_value > warn_value:
            return operator.ge

    def check_record(self, record):
        if record.target in self.exclude:
            return Level.NOMINAL, 'Excluded'
        try:
            value = record.get_average()
        except NoDataError:
            return 'NO DATA', 'No data'
        if self.comparison_operator(value, self.critical):
            return Level.CRITICAL, value
        elif self.comparison_operator(value, self.warning):
            return Level.WARNING, value
        return Level.NOMINAL, value

    def value_for_level(self, level):
        if level == Level.CRITICAL:
            return self.critical
        elif level in (Level.WARNING, Level.NOMINAL):
            return self.warning
        else:
            return None


def contents_of_file(filename):
    open_file = open(filename)
    contents = open_file.read()
    open_file.close()
    return contents


def get_alerts(path):
    alert_yml = contents_of_file(path)
    alert_strings = load(alert_yml)
    alerts = []
    for alert_string in alert_strings['alerts']:
        alerts.append(Alert(alert_string))
    return alerts

if __name__ == '__main__':
    print get_alerts()
