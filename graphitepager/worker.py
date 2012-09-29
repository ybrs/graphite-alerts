import datetime
import time
import os

import requests
import redis
from pagerduty import PagerDuty

from alerts import get_alerts
from graphite_target import get_records
from graphite_data_record import GraphiteDataRecord
from redis_storage import RedisStorage


STORAGE = RedisStorage(redis, os.getenv('REDISTOGO_URL'))

pg_key = os.getenv('PAGERDUTY_KEY')
pagerduty_client = PagerDuty(pg_key)

GRAPHITE_URL = os.getenv('GRAPHITE_URL')


def get_metric_from_graphite_url(url):
    user = os.environ['GRAPHITE_USER']
    password = os.environ['GRAPHITE_PASS']

    print 'checking', url
    r = requests.get(url, auth=('user', 'pass'), verify=False)
    return GraphiteDataRecord(r.content)


def update_pd(alert, record):
    incident = STORAGE.get_incident_key_for_alert_and_record(alert, record)
    alert_level = alert.check_value(record.avg)
    alert_template = '{2} alert for {0}! "{0}" is at {1}'
    alert_string = alert_template.format(alert.name, record.avg, alert_level)
    if alert_level is None and incident is not None:
        pagerduty_client.resolve(incident_key=incident)
        STORAGE.remove_incident_for_alert_and_record(alert, record)

    if alert_level:
        incident = pagerduty_client.trigger(incident_key=incident, description=alert_string)
        STORAGE.set_incident_key_for_alert_and_record(alert, record, incident)


def run():
    alerts = get_alerts()
    while True:
        for alert in alerts:
            target = alert.target
            records = get_records(
               GRAPHITE_URL,
               requests.get,
               GraphiteDataRecord,
               target
            )

            for record in records:
                name = alert.name
                update_pd(alert, record)
        print 'Sleeping for 60 seconds at', datetime.datetime.utcnow()
        time.sleep(60)

if __name__ == '__main__':
    run()
