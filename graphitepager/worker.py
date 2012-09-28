import datetime
import time
import os

import requests
import redis
from pagerduty import PagerDuty

from alerts import get_alerts
from graphite_target import get_records
from graphite_data_record import GraphiteDataRecord


redis_url = os.getenv('REDISTOGO_URL')
redis_client = redis.from_url(redis_url)

pg_key = os.getenv('PAGERDUTY_KEY')
pagerduty_client = PagerDuty(pg_key)

GRAPHITE_URL = os.getenv('GRAPHITE_URL')


def get_metric_from_graphite_url(url):
    user = os.environ['GRAPHITE_USER']
    password = os.environ['GRAPHITE_PASS']

    print 'checking', url
    r = requests.get(url, auth=('user', 'pass'), verify=False)
    return GraphiteDataRecord(r.content)


def publish_alert(name, value, level):
    incident_key = redis_client.get(name)

    alert_string = '{2} alert for {0}! "{0}" is at {1}'.format(name, value, level)
    print alert_string
    incident_key = pagerduty_client.trigger(incident_key=incident_key, description=alert_string)
    redis_client.set(name, incident_key)
    redis_client.expire(name, 300)

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

            for data in records:
                name = alert.name
                alert_response = alert.check_value(data.avg)
                if alert_response is None:
                    print 'Everything is fine for', name
                else:
                    publish_alert(name, data.avg, alert_response)
        print 'Sleeping for 60 seconds at', datetime.datetime.utcnow()
        time.sleep(60)

if __name__ == '__main__':
    run()
