from ..level import Level


class MailNotifier(object):

    name = 'mail'

    def __init__(self, client, storage):
        self._client = client
        self._storage = storage

    def notify(self, alert_key, level, description, html_description):
        pass