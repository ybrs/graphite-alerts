import logging
from ..level import Level

log = logging.getLogger('notifiers.mail')

class MailNotifier(object):

    name = 'mail'

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage
        log.info('Initializing MailNotifier')

    def notify(self, alert_key, level, description, html_description):
        log.info('MailNotifier not yet implemented')
        pass