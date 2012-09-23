
from uuid import uuid4
from unittest import TestCase

from mock import patch, Mock

from graphitepager.alerts import contents_of_file


class TestReadingFile(TestCase):

    def setUp(self):
        self.file_contents = str(uuid4())
        self.filename = 'FILENAME'
        with patch('__builtin__.open') as open_mock:
            open_mock().read.return_value = self.file_contents
            self.open_mock = open_mock
            self.returned = contents_of_file(self.filename)

    def test_opens_filename(self):
        self.open_mock.assert_called_with(self.filename)

    def test_contents_returned(self):
        self.assertEquals(self.returned, self.file_contents)
