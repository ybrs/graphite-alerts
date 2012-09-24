import datetime
import time
import os

import requests
import redis
from pagerduty import PagerDuty

from alerts import get_alerts
from graphite_data_record import GraphiteDataRecord

redis_url = os.getenv('REDISTOGO_URL')
redis_client = redis.from_url(redis_url)

pg_key = os.getenv('PAGERDUTY_KEY')
pagerduty_client = PagerDuty(pg_key)

def graphite_url_for_target(target):
    base = 'http://graphite.seatgeek.com/render'
    return '{0}/?target={1}&rawData=true&from=-1min'.format(base, target)

def get_metric_from_graphite_url(url):
    user = os.environ['GRAPHITE_USER']
    password = os.environ['GRAPHITE_PASS']

    print 'checking', url
    r = requests.get(url, auth=('user', 'pass'), verify=False)
    return GraphiteDataRecord(r.content)


def publish_alert(name, value, level):
    incident_key = redis_client.get(name)

    alert_string = 'alert! {0} is greater than warning {1} for "{0}", the actual value is {2}'.format(name, value, level)
    print alert_string
    incident_key = pagerduty_client.trigger(incident_key=incident_key, description=alert_string)
    redis_client.set(name, incident_key)
    redis_client.expire(name, 300)

def run():
    alerts = get_alerts()
    while True:
        for alert in alerts:
            target = alert['target']
            url = graphite_url_for_target(target)
            data = get_metric_from_graphite_url(url)
            name = alert['name']
            if data.avg > alert['warning']:
                publish_alert(name, alert['warning'], data.avg)
            else:
                print 'Everything is fine for', name
        print 'Sleeping for 60 seconds at', datetime.datetime.utcnow()
        time.sleep(60)

if __name__ == '__main__':
    run()
