class NotifierProxy(object):

    def __init__(self):
        self._notifiers = []

    def add_notifier(self, notifier):
        self._notifiers.append(notifier)
        pass

    def notify(self, *args, **kwargs):
        for notifier in self._notifiers:
            notifier.notify(*args, **kwargs)
