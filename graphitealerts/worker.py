
import argparse
import os
import time
import logging

from urllib import urlencode
from datetime import datetime
from hipchat import HipChat
from jinja2 import Template
from pagerduty import PagerDuty
import yaml
import redis
import requests.exceptions

from .alerts import Alert
from .graphite_data_record import GraphiteDataRecord
from .graphite_target import get_records
from .level import Level
from .notifier_proxy import NotifierProxy
from .redis_storage import RedisStorage
from .notifiers.console import ConsoleNotifier
from .notifiers.log import LogNotifier
from .notifiers.pagerduty import PagerdutyNotifier
from .notifiers.hipchat import HipchatNotifier

settings = {}

log = logging.getLogger('worker')

ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}. You are getting this alert because {{current_value}} matches rule: {{rule}} Go to {{graph_url}}. """

HTML_ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.  
You are getting this alert because {{current_value}} matches rule: <br>
{{rule}} 
Go to <a href="{{graph_url}}">the graph</a>
"""

def description_for_alert(template, alert, record, level, current_value, rule):
    context = dict(locals())
    context['graphite_url'] = settings['graphite_url']    
    context['rule'] = rule['description']
    url_params = (
        ('width', 586),
        ('height', 308),
        ('target', alert.target),
        ('from', '-20mins')
    )
    url_args = urlencode(url_params)
    url = '{}/render/?{}'.format(settings['graphite_url'], url_args)
    context['graph_url'] = url.replace('https', 'http')
    return Template(template).render(context)


class Description(object):

    def __init__(self, template, alert, record, level, value, rule):
        self.template = template
        self.alert = alert
        self.record = record
        self.level = level
        self.value = value
        self.rule = rule

    def __str__(self):
        return description_for_alert(
            self.template,
            self.alert,
            self.record,
            self.level,
            self.value,
            self.rule
        )

def update_notifiers(alert, record, history_records=None):
    alert_key = '{} {}'.format(alert.name, record.target)
    
    alert_level, value, rule = alert.check_record(record, history_records)

    if alert_level != Level.NOMINAL:
        description = Description(ALERT_TEMPLATE, alert, record, alert_level, value, rule)
        html_description = Description(HTML_ALERT_TEMPLATE, alert, record, alert_level, value, rule)
        log.debug('alert description %s', description)
        notifier_proxy.notify(alert_key, alert_level, description, html_description)

def get_args_from_cli():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument('--config', '-c', metavar='config', type=str, nargs=1, default='alerts.yml', help='path to the config file')
    parser.add_argument('--redisurl', metavar='redisurl', type=str, nargs=1, default='redis://localhost:6379', help='redis host')
    parser.add_argument('--pagerduty-key', metavar='pagerduty_key', type=str, nargs=1, default='', help='pagerduty key')
    parser.add_argument('--hipchat-key', metavar='hipchat_key', type=str, nargs=1, default='', help='hipchat key')
    parser.add_argument('--graphite-url', metavar='graphite_url', type=str, 
                            default='', help='graphite url')
    args = parser.parse_args()
    return args


notifier_proxy = NotifierProxy()


def contents_of_file(filename):
    try:
        open_file = open(filename)
    except:
        raise Exception("couldnt open config file, %s " % filename)
    contents = open_file.read()
    open_file.close()
    return contents


def get_config(path):
    log.info('Using %s for alert configuration', path)
    alert_yml = contents_of_file(path)
    config = yaml.load(alert_yml)
    alerts = []
    doc_url = config.get('docs_url')
    settings = config['settings'] 
    for alert_string in config['alerts']:
        log.info('alert %s is being set up', alert_string)
        alerts.append(Alert(alert_string, doc_url))
    return alerts, settings

from .graphite_target import graphite_url_for_historical_data

def check_for_alert(alert):
    global seen_alert_targets
    
    auth = None
    try:
        auth = (settings['graphite_auth_user'], settings['graphite_auth_password'])
    except KeyError:
        pass 
    
    target = alert.target
    history_records = None
    try:
        if alert.check_method == 'historical':
            history_records = get_records(settings['graphite_url'],                                                 
                                         target,
                                         auth=auth,
                                         from_=alert.smart_average_from,
                                         url_fn=graphite_url_for_historical_data,
                                         historical_fn = alert.historical
                                         )
            
        records = get_records(settings['graphite_url'], 
                              target, auth=auth, 
                              from_=alert.from_)
    except requests.exceptions.RequestException as exc:
        notification = 'Could not get target: {}'.format(target)
        log.warning(notification)
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
        k = '%s:%s' % (name, target)
        ts = time.time()
        if k not in seen_alert_targets:
            log.debug('Checking %s %s', name, target)
            update_notifiers(alert, record, history_records)
            seen_alert_targets[k] = (name, target, ts)            
        else:            
            log.debug('Seen %s %s', name, target)
    
seen_alert_targets = {}

def remove_old_seen_alerts():
    r = []
    for k, v in seen_alert_targets.iteritems():
        name, target, ts = v
        now = time.time()
        if (now - ts) > 300:
            # after 5 mins remove the seen targets so they can give alerts
            # again
            r.append(k)  
    for i in r:
        del seen_alert_targets[i]
        
def run():
    '''
    Worker runner that checks for alerts.
    '''

    global notifier_proxy, settings
    args = get_args_from_cli()    
    alerts, settings = get_config(args.config[0])

    # setting up logging
    if not 'log_file' in settings:
        settings['log_file'] = 'graphite-alerts.log'

    if not 'log_level' in settings:
        settings['log_level'] = logging.WARNING
    else:
        settings['log_level'] = settings['log_level'].upper()

    if not 'log_format' in settings:
        settings['log_format'] = '%(asctime)s %(name)s %(levelname)s %(message)s'

    if not 'log_datefmt' in settings:
        settings['log_datefmt'] = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(filename=settings['log_file'], level=settings['log_level'], format=settings['log_format'], datefmt=settings['log_datefmt'])

    log.info('graphite-alerts started')
    log.debug('Command line arguments:')
    log.debug(args)

    log.debug('Initializing redis at %s', args.redisurl)
    STORAGE = RedisStorage(redis, args.redisurl)

    notifier_proxy.add_notifier(LogNotifier(STORAGE))
    notifier_proxy.add_notifier(ConsoleNotifier(STORAGE))

    settings['graphite_url'] = args.graphite_url or settings['graphite_url']          
    settings['pagerduty_key'] = args.pagerduty_key or settings['pagerduty_key']
    log.debug('graphite_url: %s', settings['graphite_url'])
    log.debug('pagerduty_key: %s', settings['pagerduty_key'])
    
    if settings['pagerduty_key']:        
        pagerduty_client = PagerDuty(settings['pagerduty_key'])
        notifier_proxy.add_notifier(PagerdutyNotifier(pagerduty_client, STORAGE))    
    
    if args.hipchat_key:
        hipchat = HipchatNotifier(HipChat(args.hipchat_key), STORAGE)
        hipchat.add_room(settings['hipchat_room'])
        notifier_proxy.add_notifier(hipchat)            
    
    while True:
        start_time = time.time()
        seen_alert_targets = set()
        for alert in alerts:
            check_for_alert(alert)
                    
        remove_old_seen_alerts()
        
        # what if cron should trigger us ?
        time_diff = time.time() - start_time
        sleep_for = 60 - time_diff
        if sleep_for > 0:
            sleep_for = 60 - time_diff
            log.info('Sleeping for %s seconds at %s', sleep_for, datetime.utcnow())
            time.sleep(60 - time_diff)

if __name__ == '__main__':
    run()
