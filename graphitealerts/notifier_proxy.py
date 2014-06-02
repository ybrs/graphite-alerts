class NotifierProxy(object):

    def __init__(self):
        self._notifiers = {}

    def add_notifier(self, name, notifier):
        self._notifiers[name] = notifier

    def notify(self, *args, **kwargs):
        for name, notifier in self._notifiers.iteritems():
            notifier.notify(*args, **kwargs)
