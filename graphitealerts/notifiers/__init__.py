class Notifier(object):
    name = 'base'

    @classmethod
    def get_instance(cls, **kwargs):
        """
        you need to override this if you want to pass parameters to
        your notifier from config.
        """
        return cls()