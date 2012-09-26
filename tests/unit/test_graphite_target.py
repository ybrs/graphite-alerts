from unittest import TestCase

from mock import call, MagicMock
import requests

from graphitepager.graphite_data_record import GraphiteDataRecord
from graphitepager.graphite_target import get_records

SAMPLE_1 = 'stat.one,1348346250,1348346310,10|2.8,0.6,2.0,3.8,3.5,3.4'
SAMPLE_2 = 'stat.two,1348346250,1348346310,10|2.8,0.6,2.0,3.8,3.5,3.4'

SAMPLE_RESPONSE = SAMPLE_1 + '\n\n' + SAMPLE_2


class TestGraphiteTarget(TestCase):

    def setUp(self):
        self.base_url = 'BASE_URL'
        self.record_class = MagicMock(GraphiteDataRecord)
        self.http_get = MagicMock(requests.get)
        self.http_get().content = SAMPLE_RESPONSE
        self.target = 'TARGET'

        self.records = get_records(
            self.base_url,
            self.http_get,
            self.record_class,
            self.target,
        )

    def test_hits_correct_url(self):
        url = 'BASE_URL/render/?target=TARGET&rawData=true&from=-1min'
        self.http_get.assert_called_with(url, verify=False)

    def should_create_two_records(self):
        calls = [call(SAMPLE_1), call(SAMPLE_2)]
        self.assertEqual(self.record_class.call_args_list, calls)

    def should_return_data_records(self):
        self.assertEqual(self.records[0], self.record_class(SAMPLE_1))
        self.assertEqual(self.records[1], self.record_class(SAMPLE_2))
