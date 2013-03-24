from urllib import urlencode
import argparse
import datetime
import os
import time

from hipchat import HipChat
from jinja2 import Template
from pagerduty import PagerDuty

import yaml
import redis
import requests
import requests.exceptions

from .alerts import Alert
from .graphite_data_record import GraphiteDataRecord
from .graphite_target import get_records
from .level import Level
from .notifier_proxy import NotifierProxy
from .redis_storage import RedisStorage
from .notifiers.console import ConsoleNotifier
from .notifiers.pagerduty import PagerdutyNotifier
from .notifiers.hipchat import HipchatNotifier

settings = {}

ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.  The
current value is {{current_value}} which passes the {{threshold_level|lower}} value of
{{threshold_value}}. Go to {{graph_url}}.
{% if docs_url %}Documentation: {{docs_url}}{% endif %}.
"""

HTML_ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.
The current value is {{current_value}} which passes the {{threshold_level|lower}} value of
{{threshold_value}}. Go to <a href="{{graph_url}}">the graph</a>.
{% if docs_url %}<a href="{{docs_url}}">Documentation</a>{% endif %}.
"""

def description_for_alert(template, alert, record, level, current_value):
    context = dict(locals())
    context['graphite_url'] = settings['graphite_url']
    context['docs_url'] = alert.documentation_url(record.target)
    url_params = (
        ('width', 586),
        ('height', 308),
        ('target', alert.target),
        ('target', 'threshold({},"Warning")'.format(alert.warning)),
        ('target', 'threshold({},"Critical")'.format(alert.critical)),
        ('from', '-20mins'),
    )
    url_args = urlencode(url_params)
    url = '{}/render/?{}'.format(settings['graphite_url'], url_args)
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
    parser.add_argument('--redisurl', metavar='redisurl', type=str, nargs=1, default='redis://localhost:6379', help='redis host')
    parser.add_argument('--pagerduty-key', metavar='pagerduty_key', type=str, nargs=1, default='', help='pagerduty key')
    parser.add_argument('--hipchat-key', metavar='hipchat_key', type=str, nargs=1, default='', help='hipchat key')
    parser.add_argument('--graphite-url', metavar='graphite_url', type=str, 
                            default='', help='graphite url')
    args = parser.parse_args()
    return args


notifier_proxy = NotifierProxy()


def contents_of_file(filename):
    open_file = open(filename)
    contents = open_file.read()
    open_file.close()
    return contents


def get_config(path):
    alert_yml = contents_of_file(path)
    config = yaml.load(alert_yml)
    alerts = []
    doc_url = config.get('docs_url')
    settings = config['settings'] 
    for alert_string in config['alerts']:
        alerts.append(Alert(alert_string, doc_url))
    return alerts, settings


def run():
    global notifier_proxy, settings
    args = get_args_from_cli()    
    print args
    alerts, settings = get_config(args.config[0])
    STORAGE = RedisStorage(redis, args.redisurl)
    settings['graphite_url'] = args.graphite_url or settings['graphite_url']          
    notifier_proxy.add_notifier(ConsoleNotifier(STORAGE))  
    
    if args.pagerduty_key:
        pagerduty_client = PagerDuty(args.pagerduty_key)
        notifier_proxy.add_notifier(PagerdutyNotifier(pagerduty_client, STORAGE))    
    
    if args.hipchat_key:
        hipchat = HipchatNotifier(HipChat(args.hipchat_key), STORAGE)
        hipchat.add_room(settings['hipchat_room'])
        notifier_proxy.add_notifier(hipchat)        
    
    auth = None
    try:
        auth = (settings['graphite_auth_user'], settings['graphite_auth_password'])
    except KeyError:
        pass 
    
    while True:
        start_time = time.time()
        seen_alert_targets = set()
        for alert in alerts:
            target = alert.target
            
            try:
                records = get_records(
                   settings['graphite_url'],
                   requests.get,
                   GraphiteDataRecord,
                   target,
                   auth=auth,
                   from_=alert.from_
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
