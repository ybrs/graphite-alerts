import json
class NotifierProxy(object):

    def __init__(self):
        self._notifiers = {}

    def add_notifier(self, name, notifier):
        self._notifiers[name] = notifier

    def notify(self, alert, *args, **kwargs):
        for name, notifier in self._notifiers.iteritems():
            if name in alert.notifiers or not alert.notifiers:
                notifier.notify(*args, **kwargs)
