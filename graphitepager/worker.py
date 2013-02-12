from urllib import urlencode
import argparse
import datetime
import os
import time

from hipchat import HipChat
from jinja2 import Template
from pagerduty import PagerDuty
import redis
import requests
import requests.exceptions

from alerts import get_alerts
from graphite_data_record import GraphiteDataRecord
from graphite_target import get_records
from hipchat_notifier import HipchatNotifier
from level import Level
from notifier_proxy import NotifierProxy
from pagerduty_notifier import PagerdutyNotifier
from redis_storage import RedisStorage


STORAGE = RedisStorage(redis, os.getenv('REDISTOGO_URL'))

pg_key = os.getenv('PAGERDUTY_KEY')
pagerduty_client = PagerDuty(pg_key)

GRAPHITE_URL = os.getenv('GRAPHITE_URL')

notifier_proxy = NotifierProxy()
notifier_proxy.add_notifier(
    PagerdutyNotifier(pagerduty_client, STORAGE))


if 'HIPCHAT_KEY' in os.environ:
    hipchat = HipchatNotifier(HipChat(os.getenv('HIPCHAT_KEY')), STORAGE)
    hipchat.add_room(os.getenv('HIPCHAT_ROOM'))
    notifier_proxy.add_notifier(hipchat)

ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.  The
current value is {{current_value}} which passes the {{threshold_level|lower}} value of
{{threshold_value}}. Go to {{graph_url}}.
"""
HTML_ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.
The current value is {{current_value}} which passes the {{threshold_level|lower}} value of
{{threshold_value}}. Go to <a href="{{graph_url}}">the graph</a>.
"""

def description_for_alert(template, alert, record, level, current_value):
    context = dict(locals())
    context['graphite_url'] = GRAPHITE_URL
    url_params = (
        ('width', 586),
        ('height', 308),
        ('target', alert.target),
        ('target', 'threshold({},"Warning")'.format(alert.warning)),
        ('target', 'threshold({},"Critical")'.format(alert.critical)),
        ('from', '-20mins'),
    )
    url_args = urlencode(url_params)
    url = '{}/render/?{}'.format(GRAPHITE_URL, url_args)
    context['graph_url'] = url.replace('https', 'http')
    context['threshold_value'] = alert.value_for_level(level)
    if level == Level.NOMINAL:
        context['threshold_level'] = 'warning'
    else:
        context['threshold_level'] = level

    return Template(template).render(context)


class Description(object):

    def __init__(self, template, alert, record, level, value):
        self.template = template
        self.alert = alert
        self.record = record
        self.level = level
        self.value = value


    def __str__(self):
        return description_for_alert(
            self.template,
            self.alert,
            self.record,
            self.level,
            self.value,
        )

def update_notifiers(alert, record):
    alert_key = '{} {}'.format(alert.name, record.target)

    alert_level, value = alert.check_record(record)

    description = Description(ALERT_TEMPLATE, alert, record, alert_level, value)
    html_description = Description(HTML_ALERT_TEMPLATE, alert, record, alert_level, value)
    if alert_level != Level.NOMINAL:
        print description

    notifier_proxy.notify(alert_key, alert_level, description, html_description)


def get_args_from_cli():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument('--config', metavar='config', type=str, nargs=1, default='alerts.yml', help='path to the config file')

    args = parser.parse_args()
    return args


def run():
    args = get_args_from_cli()
    alerts = get_alerts(args.config[0])
    while True:
        start_time = time.time()
        seen_alert_targets = set()
        for alert in alerts:
            target = alert.target
            try:
                records = get_records(
                   GRAPHITE_URL,
                   requests.get,
                   GraphiteDataRecord,
                   target,
                   from_=alert.from_,
                )
            except requests.exceptions.RequestException as exc:
                notification = 'Could not get target: {}'.format(target)
                print notification
                notifier_proxy.notify(
                    target,
                    Level.CRITICAL,
                    notification,
                    notification,
                )
                records = []

            for record in records:
                name = alert.name
                target = record.target
                if (name, target) not in seen_alert_targets:
                    print 'Checking', (name, target)
                    update_notifiers(alert, record)
                    seen_alert_targets.add((name, target))
                else:
                    print 'Seen', (name, target)
        time_diff = time.time() - start_time
        sleep_for = 60 - time_diff
        if sleep_for > 0:
            sleep_for = 60 - time_diff
            print 'Sleeping for {0} seconds at'.format(sleep_for), datetime.datetime.utcnow()
            time.sleep(60 - time_diff)

if __name__ == '__main__':
    run()
