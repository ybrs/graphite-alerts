import datetime
import time
import os

import requests

from alerts import get_alerts
from graphite_data_record import GraphiteDataRecord


def graphite_url_for_target(target):
    base = 'http://graphite.seatgeek.com/render'
    return '{0}/?target={1}&rawData=true&from=-1min'.format(base, target)

def get_metric_from_graphite_url(url):
    user = os.environ['GRAPHITE_USER']
    password = os.environ['GRAPHITE_PASS']

    print 'checking', url
    r = requests.get(url, auth=('user', 'pass'), verify=False)
    return r.content



def run():
    alerts = get_alerts()
    while True:
        for alert in alerts:
            target = alert['target']
            url = graphite_url_for_target(target)
            data = get_metric_from_graphite_url(url)
            if data > alert['warning']:
                print 'alert! {0} is greater than warning {1} for {2}'.format(alert['name'], alert['warning'], alert['name'])
            else:
                print 'Everything is fine for', alert['name']
        print 'Sleeping for 60 seconds at', datetime.datetime.utcnow()
        time.sleep(60)

if __name__ == '__main__':
    run()
