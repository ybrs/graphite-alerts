
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
from .graphite_target import get_records, graphite_url_for_historical_data
from .level import Level
from .notifier_proxy import NotifierProxy
from .redis_storage import RedisStorage
import pickle

settings = {}

log = logging.getLogger('worker')

ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}. You are getting this alert because {{current_value}} matches rule: {{rule}} Go to {{graph_url}}. """

HTML_ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.
You are getting this alert because {{current_value}} matches rule: <br>
{{rule}}
Go to <a href="{{graph_url}}">the graph</a>
"""

def description_for_alert(app, template, alert, record, level, current_value, rule):
    context = dict(locals())
    context['graphite_url'] = app.settings['graphite_url']
    context['rule'] = rule['description']
    url_params = (
        ('width', 586),
        ('height', 308),
        ('target', record.target),
        ('from', '-20mins')
    )
    url_args = urlencode(url_params)
    url = '{}/render/?{}'.format(app.settings['graphite_url'], url_args)
    context['graph_url'] = url.replace('https', 'http')
    return Template(template).render(context)


class Description(object):

    def __init__(self, app, template, alert, record, level, value, rule):
        self.app = app
        self.template = template
        self.alert = alert
        self.record = record
        self.level = level
        self.value = value
        self.rule = rule

    def __str__(self):
        return description_for_alert(
            self.app,
            self.template,
            self.alert,
            self.record,
            self.level,
            self.value,
            self.rule
        )


def get_args_from_cli():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument('--config', '-c',
                        metavar='config',
                        default='alerts.yml',
                        help='path to the config file')
    parser.add_argument('--redisurl', metavar='redisurl', type=str, nargs=1,
                        default='redis://localhost:6379', help='redis host')
    parser.add_argument('--pagerduty-key', metavar='pagerduty_key', type=str, nargs=1,
                        default='', help='pagerduty key')
    parser.add_argument('--hipchat-key', metavar='hipchat_key', type=str, nargs=1,
                        default='', help='hipchat key')
    parser.add_argument('--graphite-url', metavar='graphite_url', type=str,
                            default='', help='graphite url')
    args = parser.parse_args()
    return args

def contents_of_file(filename):
    try:
        open_file = open(filename)
    except:
        print "----------------------------------------"
        print "Couldn't open config file %s " % filename
        print "please start with graphite-alerts -c configfile.yml"
        print "----------------------------------------"
        raise Exception("couldn't open config file, %s " % filename)
    contents = open_file.read()
    open_file.close()
    return contents

class DummyRecord(object):
    def __init__(self, target):
        self.values = ['lost_metric']
        self.target = target

class Application(object):
    """
    this is the global application object, we pass this to notifiers, hold configs etc.
    """
    def __init__(self):
        self.notifier_proxy = NotifierProxy()
        self.notifiers = {}
        self.settings = {}
        self.seen_alert_targets = {}

    def get_config(self, path):
        log.info('Using %s for alert configuration', path)
        alert_yml = contents_of_file(path)
        config = yaml.load(alert_yml)
        alerts = []
        doc_url = config.get('docs_url')
        settings = config['settings']
        notifiers = config['notifiers']
        for alert_string in config['alerts']:
            log.info('alert %s is being set up', alert_string)
            alerts.append(Alert(self, alert_string, doc_url))
        return alerts, settings, notifiers

    def remove_old_seen_alerts(self):
        r = []
        for k, v in self.seen_alert_targets.iteritems():
            name, target, ts = v
            now = time.time()
            if (now - ts) > 300:
                # after 5 mins remove the seen targets so they can give alerts
                # again
                r.append(k)
        for i in r:
            del self.seen_alert_targets[i]


    def collect_notifiers(self, notifier_settings):
        import inspect
        notifiers_folder = os.path.join(os.path.dirname(__file__), 'notifiers')
        from graphitealerts.notifiers import Notifier
        files = os.listdir(notifiers_folder)
        notifier_classes = {}
        for file in files:
            if file.endswith('.py'):
                mdlname = 'graphitealerts.notifiers.%s' % file.split('.')[0]
                mdl = __import__(mdlname, fromlist=[''])
                clsmembers = inspect.getmembers(mdl, inspect.isclass)
                for name, cls in clsmembers:
                    if issubclass(cls, Notifier) and cls != Notifier:
                        notifier_classes[cls.name] = cls

        for k, v in notifier_settings.iteritems():
            if v.get('disabled', False):
                continue
            name = v.get('from_class', k)
            log.debug('initializing %s notifier', name)
            print "------"
            print v
            print "------"
            log.debug("init with params %s", v)
            notifier = notifier_classes[name].get_instance(self, **v)
            self.notifiers[notifier.name] = notifier
            self.notifier_proxy.add_notifier(name, notifier)

    def update_notifiers(self, alert, record, history_records=None):
        alert_key = '{} {}'.format(alert.name, record.target)
        print "--- .... ---"
        print record, history_records
        c = alert.check_record(self, record, history_records)

    def check_for_alert(self, alert):
        auth = None
        try:
            auth = (self.settings['graphite_auth_user'], self.settings['graphite_auth_password'])
        except KeyError:
            pass

        target = alert.target
        history_records = None
        try:
            if alert.check_method == 'historical':
                history_records = get_records(self.settings['graphite_url'],
                                             target,
                                             auth=auth,
                                             from_=alert.smart_average_from,
                                             url_fn=graphite_url_for_historical_data,
                                             historical_fn = alert.historical
                                             )

            records = get_records(self.settings['graphite_url'],
                                  target, auth=auth,
                                  from_=alert.from_)
        except requests.exceptions.RequestException as exc:
            notification = 'Could not get target: {}'.format(target)
            log.warning(notification)
            log.exception(exc)
            self.notifier_proxy.notify(
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
            self.storage._client.hset('graphite_alerts_%s' % alert.target, record.target, pickle.dumps(datetime.utcnow()))

            if k not in self.seen_alert_targets:
                log.debug('Checking %s %s', name, target)
                self.update_notifiers(alert, record, history_records)
                self.seen_alert_targets[k] = (name, target, ts)
            else:
                log.debug('Seen %s %s', name, target)

        recs = self.storage._client.hgetall('graphite_alerts_%s' % alert.target)
        now = datetime.utcnow()
        for k, v in recs.iteritems():
            if (now - pickle.loads(v)).seconds > 300:
                print "we havent seen %s for %s seconds" %  (k, (now - pickle.loads(v)).seconds)
                r = DummyRecord(target=k)
                self.update_notifiers(alert, r, history_records)

def run():
    '''
    Worker runner that checks for alerts.
    '''
    args = get_args_from_cli()

    app = Application()
    alerts, settings, notifier_settings = app.get_config(args.config)

    # setting up logging
    if not 'log_level' in settings:
        settings['log_level'] = logging.WARNING
    else:
        settings['log_level'] = settings['log_level'].upper()

    if not 'log_format' in settings:
        settings['log_format'] = '%(asctime)s %(name)s %(levelname)s %(message)s'

    if not 'log_datefmt' in settings:
        settings['log_datefmt'] = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(filename=settings.get('log_file', None),
                        level=settings['log_level'],
                        format=settings['log_format'],
                        datefmt=settings['log_datefmt'])

    log.info('graphite-alerts started')
    log.debug('Command line arguments:')
    log.debug(args)

    app.storage = RedisStorage(redis, args.redisurl)
    app.settings = settings

    log.debug('Initializing redis at %s', args.redisurl)
    app.collect_notifiers(notifier_settings)

    settings['graphite_url'] = args.graphite_url or settings['graphite_url']
    if settings['graphite_url'].endswith('/'):
        settings['graphite_url'] = settings['graphite_url'][:-1]

    log.debug('graphite_url: %s', settings['graphite_url'])

    while True:
        start_time = time.time()
        for alert in alerts:
            app.check_for_alert(alert)

        app.remove_old_seen_alerts()

        # what if cron should trigger us ?
        time_diff = time.time() - start_time
        sleep_for = 60 - time_diff
        if sleep_for > 0:
            sleep_for = 60 - time_diff
            log.info('Sleeping for %s seconds at %s', sleep_for, datetime.utcnow())
            time.sleep(60 - time_diff)

        if settings.get('run_once', False):
            break

if __name__ == '__main__':
    run()
