from mock import MagicMock
from unittest import TestCase

from graphitepager.graphite_data_record import GraphiteDataRecord


SAMPLE_1 = 'stat.one,1348346250,1348346310,10|2.8,0.6,2.0,3.8,3.5,3.4'

class TestGraphiteDataRecord(TestCase):

    def setUp(self):
        self.record = GraphiteDataRecord(SAMPLE_1)

    def test_metric_name(self):
        self.assertEqual(self.record.target, 'stat.one')

    def test_start_time(self):
        self.assertEqual(self.record.start_time, 1348346250)

    def test_end_time(self):
        self.assertEqual(self.record.end_time, 1348346310)

    def test_step(self):
        self.assertEqual(self.record.step, 10)


