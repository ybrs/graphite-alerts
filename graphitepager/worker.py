import datetime
import time
import os

import requests
import redis
from jinja2 import Template
from pagerduty import PagerDuty

from alerts import get_alerts
from graphite_target import get_records
from graphite_data_record import GraphiteDataRecord
from redis_storage import RedisStorage


STORAGE = RedisStorage(redis, os.getenv('REDISTOGO_URL'))

pg_key = os.getenv('PAGERDUTY_KEY')
pagerduty_client = PagerDuty(pg_key)

GRAPHITE_URL = os.getenv('GRAPHITE_URL')

ALERT_TEMPLATE = r"""{{level}} alert for {{alert.name}} {{record.target}}.
The current value is {{current_value}}

Go to {{graphite_url}}/render/?width=586&height=308&target={{alert.target}}&target=threshold%28{{alert.warning}}%2C%22Warning%22%29&target=threshold%28{{alert.critical}}%2C%22Critical%22%29&from=-20mins

"""

def description_for_alert(alert, record, level, current_value):
    context = dict(locals())
    context['graphite_url'] = GRAPHITE_URL

    return Template(ALERT_TEMPLATE).render(context)


def update_pd(alert, record):
    incident = STORAGE.get_incident_key_for_alert_and_record(alert, record)
    alert_level = alert.check_value_from_callable(record.get_average)
    if alert_level == 'NO DATA':
        value = 'None'
    else:
        value = record.get_average()
    if alert_level is None and incident is not None:
        pagerduty_client.resolve(incident_key=incident)
        STORAGE.remove_incident_for_alert_and_record(alert, record)

    if alert_level:
        alert_string = description_for_alert(alert, record, alert_level, value)
        print alert_string
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
