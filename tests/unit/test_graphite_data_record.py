from mock import MagicMock
from unittest import TestCase

from graphitepager.graphite_data_record import GraphiteDataRecord


SAMPLE_FINE = 'stat.one,1348346250,1348346310,10|1.0,2.0,3.0,4.0'
SAMPLE_NONE = 'stat.one,1348346250,1348346310,10|1.0,None'


class _BaseTest(TestCase):

    def setUp(self):
        self.record = GraphiteDataRecord(self.data)

    def test_metric_name(self):
        self.assertEqual(self.record.target, 'stat.one')

    def test_start_time(self):
        self.assertEqual(self.record.start_time, 1348346250)

    def test_end_time(self):
        self.assertEqual(self.record.end_time, 1348346310)

    def test_step(self):
        self.assertEqual(self.record.step, 10)


class TestGraphiteDataRecord(_BaseTest):

    data = SAMPLE_FINE

    def test_average_is_correct(self):
        self.assertEqual(self.record.avg, 2.5)


class TestGraphiteDataRecordWithMissingData(_BaseTest):

    data = SAMPLE_NONE

    def test_average_is_correct(self):
        self.assertEqual(self.record.avg, 1.0)
