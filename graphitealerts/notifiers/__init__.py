class Notifier(object):
    name = 'base'

    @classmethod
    def get_instance(cls, **kwargs):
        """
        you need to override this if you want to pass parameters to
        your notifier from config.
        """
        return cls()

    def notify_(self, metric_name, level, value):
        raise Exception("you need to override this")

    def already_notified(self, metric_name):
        pass

    def notify(self, metric_name, level, value):
        if not self.already_notified:
            self.notify_(metric_name, level, value)