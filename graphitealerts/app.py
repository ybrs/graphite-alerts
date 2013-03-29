import requests
import json
import yaml
import argparse
from flask import Flask, g, request, redirect
from flask.templating import render_template
from flask.ext.sqlalchemy import SQLAlchemy
from models import Graphic
from graphitealerts.models.dashboard import Dashboard

app = Flask(__name__)

@app.before_request
def get_dashboards():
    g.dashboards = Dashboard.query.all()
    

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


@app.route('/d/<id>')
@app.route('/dashboard/<id>')
def dashboard(id):    
    dashboard = Dashboard.get(id)
    graphics = Graphic.query.filter_by(dashboard_id=id).order_by('ob asc').all()
    graphs = []
    
    colwidth = 10000
    for graphic in graphics:
        data = get_data_from_graphite(graphic.url, from_=graphic.from_)
        graphs.append({'graph':graphic, 'data':json.dumps(data)})
        if graphic.width<colwidth:
            colwidth = graphic.width
            
    return render_template('dashboard.html', graphs=graphs, dashboard=dashboard, json_dumps=json.dumps, colwidth=colwidth)

@app.route('/dashboard/new')
def dashboardnew():
    return render_template('newdashboard.html')

@app.route('/dashboard/new', methods=['POST'])
@app.route('/dashboard/<id>/save', methods=['POST'])
def dashboardsave(id=None):
    if id:
        d = Dashboard.get(id)
    else:
        d = Dashboard()
    d.title = request.form['title']
    d.save()
    return redirect('/d/%s' % d.id)

@app.route('/graphic/new/<dashid>', methods=['POST'])
@app.route('/graphic/<id>/save', methods=['POST'])
def graphicsave(dashid=None, id=None):    
    if id:
        d = Graphic.get(id)
        dash = Dashboard.get(d.dashboard_id)
    else:
        dash = Dashboard.get(dashid)
        d = Graphic()
        d.dashboard_id = dash.id
    d.title = request.form['title']
    d.width = request.form['width']
    d.height = request.form['height']
    d.source = 'graphite'
    d.url = request.form['url']
    d.from_ = request.form['from']
    d.graphtype = request.form['graphtype']        
    d.save()
    print "saved : ", d.id
    return redirect('/d/%s' % dash.id)


@app.route('/')
def hello_world():    
    graphics = Graphic.query.filter_by(dashboard_id=1).order_by('ob asc').all()
    for graphic in graphics:
        data = get_data_from_graphite(graphic.url, from_=graphic.from_)    
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