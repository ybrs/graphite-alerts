from yaml import load, dump

def contents_of_file(filename):
    open_file = open(filename)
    contents = open_file.read()
    open_file.close()
    return contents


def get_alerts():

    alert_yml = contents_of_file('alerts.yml')
    alerts = load(alert_yml)
    return alerts['alerts']

if __name__ == '__main__':
    print get_alerts()
