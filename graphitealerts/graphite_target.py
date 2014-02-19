import requests
import logging
from graphite_data_record import GraphiteDataRecord

log = logging.getLogger('graphite_target')

def graphite_url_for_historical_data(base, target, from_, historical_fn):
    fn, from_ = historical_fn.split('from')
    target = fn.replace('target', target)
    return '{0}/render/?target={1}&rawData=true&from={2}'.format(base, target, from_)

def _graphite_url_for_target(base, target, from_='-1min'):
    return '{0}/render/?target={1}&rawData=true&from={2}'.format(base, target, from_)

def get_records(base_url, target, auth=None, url_fn=_graphite_url_for_target, **kwargs):    
    url = url_fn(base_url, target, **kwargs)
    log.debug('asking url %s', url)
    historical = not(url_fn == _graphite_url_for_target)
    resp = requests.get(url, auth=auth, verify=False)
    resp.raise_for_status()
    records = []
    for line in resp.content.split('\n'):
        log.debug(line)
        if line:
            record = GraphiteDataRecord(line, historical=historical)
            records.append(record)
    return records


