
def graphite_url_for_historical_data(base, target, from_, historical_fn):
    fn, from_ = historical_fn.split('from')
    target = fn.replace('target', target)
    return '{0}/render/?target={1}&rawData=true&from={2}'.format(base, target, from_)

def _graphite_url_for_target(base, target, from_='-1min'):
    return '{0}/render/?target={1}&rawData=true&from={2}'.format(base, target, from_)

def get_records(base_url, http_get, data_record, target, auth=None, url_fn=_graphite_url_for_target, **kwargs):    
    url = url_fn(base_url, target, **kwargs)
    print "asking url>>>", url
    
    resp = http_get(url, auth=auth, verify=False)
    
    resp.raise_for_status()
    records = []
    for line in resp.content.split('\n'):
        print line
        if line:
            record = data_record(line)
            records.append(record)
    return records


