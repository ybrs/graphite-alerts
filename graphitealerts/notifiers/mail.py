import logging
from ..level import Level
from . import Notifier
log = logging.getLogger('notifiers.mail')

class MailNotifier(Notifier):

    name = 'mail'

    @classmethod
    def get_instance(cls, app, *args, **kwargs):
        return cls(app.storage)

    def __init__(self, storage):
        self._storage = storage
        log.info('Initializing MailNotifier')

    def notify(self, alert_key, level, description, html_description):
        log.info('MailNotifier not yet implemented')