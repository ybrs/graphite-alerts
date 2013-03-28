import requests
import json
import yaml
import argparse
from flask import Flask
from flask.templating import render_template
from flask.ext.sqlalchemy import SQLAlchemy
from models import Graphic

app = Flask(__name__)


def graphite_data_to_datapoints(data):
    """ graphite sends data in format [104.0, 1364493300], [104.0, 1364493360], [null, 1364493420], [104.0, 1364493480]
    rickshaw wants data in format [ { x: 0, y: 40 }, { x: 1, y: 49 }, { x: 2, y: 38 }, { x: 3, y: 30 }, { x: 4, y: 32 } ]
    this makes the conversion
    """
    ret = []
    for i in data:
        ret.append({'x': i[1], 'y': i[0] or 0})
    return ret

def get_data_from_graphite(target, from_='-20min'):
    url = '{0}/render/?target={1}&rawData=true&format=json&from={2}'.format(settings['graphite_url'], target, from_)
    r = requests.get(url, auth=(settings['graphite_auth_user'], settings['graphite_auth_password']))
    try:
        return json.loads(r.content)
    except:
        print "==========================="
        print r.content
        print "==========================="
        raise Exception("return data error %s" % r.content)

@app.route('/')
def hello_world():
    
    graphics = Graphic.query.filter_by(dashboard_id=1).order_by('ob asc').all()
    for graphic in graphics:
        data = get_data_from_graphite(graphic.url, from_=graphic.from_)    
    # data[0]['datapoints'] = graphite_data_to_datapoints(data[0]['datapoints'])
    return render_template('anasayfa.html', data=json.dumps(data))


def contents_of_file(filename):
    try:
        f = open(filename)
    except Exception as e:
        print e
        raise Exception("couldnt open config file, %s " % filename)
    contents = f.read()
    f.close()
    return contents

def get_config(path):    
    fstr = contents_of_file(path)
    config = yaml.load(fstr)
    settings = config['settings']
    return settings 
    

def get_args_from_cli():
    parser = argparse.ArgumentParser(description='Run Graphite Pager')
    parser.add_argument('--config', '-c', metavar='config', type=str, nargs=1, default='alerts.yml', help='path to the config file')
    parser.add_argument('--graphite-url', metavar='graphite_url', type=str, 
                            default='', help='graphite url')
    args = parser.parse_args()
    return args


settings = {}

def run():
    global settings 
    args = get_args_from_cli()
    settings = get_config(args.config[0])
    app.debug = True
    app.run()

if __name__ == '__main__':
    app.run()