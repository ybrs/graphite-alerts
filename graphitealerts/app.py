from flask import Flask
from flask.templating import render_template
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('anasayfa.html')


def run():
    app.debug = True
    app.run()

if __name__ == '__main__':
    app.run()