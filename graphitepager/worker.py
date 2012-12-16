from urllib import urlencode
import argparse
import datetime
import time
import os

import requests
import redis
from jinja2 import Template
from pagerduty import PagerDuty
from hipchat import HipChat

from alerts import get_alerts
from graphite_data_record import GraphiteDataRecord
from graphite_target import get_records
from hipchat_notifier import HipchatNotifier
from level import Level
from pagerduty_notifier import PagerdutyNotifier
from redis_storage import RedisStorage


STORAGE = RedisStorage(redis, os.getenv('REDISTOGO_URL'))

pg_key = os.getenv('PAGERDUTY_KEY')
pagerduty_client = PagerDuty(pg_key)

GRAPHITE_URL = os.getenv('GRAPHITE_URL')

NOTIFIERS = [
    PagerdutyNotifier(pagerduty_client, STORAGE)
]


if 'HIPCHAT_KEY' in os.environ:
    hipchat = HipchatNotifier(HipChat(os.getenv('HIPCHAT_KEY')), STORAGE)
    hipchat.add_room(os.getenv('HIPCHAT_ROOM'))
    NOTIFIERS.append(hipchat)

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


def update_notifiers(alert, record):
    alert_key = '{} {}'.format(alert.name, record.target)

    alert_level, value = alert.check_record(record)

    description = description_for_alert(ALERT_TEMPLATE, alert, record, alert_level, value)
    html_description = description_for_alert(HTML_ALERT_TEMPLATE, alert, record, alert_level, value)

    for notifier in NOTIFIERS:
        notifier.notify(alert_key, alert_level, description, html_description)


def get_args_from_cli():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument('--config', metavar='config', type=str, nargs=1, default='alerts.yml', help='path to the config file')

    args = parser.parse_args()
    return args


def run():
    args = get_args_from_cli()
    alerts = get_alerts(args.config[0])
    while True:
        seen_alert_targets = set()
        for alert in alerts:
            target = alert.target
            records = get_records(
               GRAPHITE_URL,
               requests.get,
               GraphiteDataRecord,
               target,
               from_=alert.from_,
            )

            for record in records:
                name = alert.name
                target = record.target
                if (name, target) not in seen_alert_targets:
                    print 'Checking', (name, target)
                    update_notifiers(alert, record)
                    seen_alert_targets.add((name, target))
                else:
                    print 'Seen', (name, target)
        print 'Sleeping for 60 seconds at', datetime.datetime.utcnow()
        time.sleep(60)

if __name__ == '__main__':
    run()
