
def get_records(base_url, http_get, data_record, target, **kwargs):
    url = _graphite_url_for_target(base_url, target, **kwargs)
    print "asking url>>>", url
    resp = http_get(url, verify=False)
    resp.raise_for_status()
    records = []
    for line in resp.content.split('\n'):
        print line
        if line:
            record = data_record(line)
            records.append(record)
    return records


def _graphite_url_for_target(base, target, from_='-1min'):
    return '{0}/render/?target={1}&rawData=true&from={2}'.format(base, target, from_)

