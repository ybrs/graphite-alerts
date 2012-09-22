from yaml import load, dump

def get_alerts():

    alert_file = open('alerts.yml').read()
    alerts = load(alert_file)
    return alerts['alerts']

if __name__ == '__main__':
    print get_alerts()
