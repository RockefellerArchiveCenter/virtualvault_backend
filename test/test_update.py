import json
from datetime import datetime
from os import getenv
from pathlib import Path
from shutil import rmtree
from unittest import TestCase
from unittest.mock import ANY, Mock, patch

from src.update import Updater


class UpdateTests(TestCase):

    @patch('src.update.Updater.__init__')
    def setUp(self, mock_init):
        mock_init.return_value = None
        self.updater = Updater()

    @patch('src.update.Updater.get_last_fetched_timestamp')
    @patch('src.update.Updater.get_refids_from_files')
    @patch('src.update.Updater.list_chunks')
    @patch('src.update.Updater.get_updated_data')
    @patch('src.update.Updater.index_data')
    @patch('src.update.Updater.set_last_fetched_timestamp')
    def test_run(self, mock_set_last_fetched, mock_index, mock_get_updated,
                 mock_list_chunks, mock_refids, mock_get_last_fetched):
        """Set up assets dir"""
        p = Path(getenv("ASSETS_DIR"))
        p.mkdir()
        for subdir in [
                "audio/00455a772f0d2c3dde0bb2847243b2e2",
                "audio/00455a772f0d2c3dde0bb2847243b2e3",
                "moving-image/00455a772f0d2c3dde0bb2847243b2e4",
                "moving-image/00455a772f0d2c3dde0bb2847243b2e5",
                "catalogued-reports/00455a772f0d2c3dde0bb2847243b2e6",
                "catalogued-reports/00455a772f0d2c3dde0bb2847243b2e7",
                "catalogued-reports/00455a772f0d2c3dde0bb2847243b2e8",]:
            (p / subdir).mkdir(parents=True)

        mock_get_last_fetched.return_value = 12345
        mock_refids.return_value = (
            ["00455a772f0d2c3dde0bb2847243b2e2"], [
                "00455a772f0d2c3dde0bb2847243b2e3", "00455a772f0d2c3dde0bb2847243b2e4"])
        mock_list_chunks.return_value = [
            "00455a772f0d2c3dde0bb2847243b2e3",
            "00455a772f0d2c3dde0bb2847243b2e4"]
        mock_get_updated.return_value = [{"foo": "bar"}, {"baz": "buz"}]

        self.updater.run()

        mock_get_last_fetched.assert_called_once_with(
            "last_fetched_timestamp.txt")

        self.assertAlmostEqual(mock_refids.call_count, 3)
        mock_refids.assert_any_call(Path("assets/moving-image"), 12345)
        mock_refids.assert_any_call(Path("assets/audio"), 12345)
        mock_refids.assert_any_call(Path("assets/catalogued-reports"), 12345)

        self.assertEqual(mock_list_chunks.call_count, 6)
        mock_list_chunks.assert_any_call(['00455a772f0d2c3dde0bb2847243b2e2'])
        mock_list_chunks.assert_any_call(
            ['00455a772f0d2c3dde0bb2847243b2e3', '00455a772f0d2c3dde0bb2847243b2e4'])
        self.assertEqual(mock_get_updated.call_count, 12)
        mock_get_updated.assert_any_call(
            '00455a772f0d2c3dde0bb2847243b2e3', 12345)
        mock_get_updated.assert_any_call(
            '00455a772f0d2c3dde0bb2847243b2e4', 12345)
        mock_get_updated.assert_any_call('00455a772f0d2c3dde0bb2847243b2e3', 0)
        mock_get_updated.assert_any_call('00455a772f0d2c3dde0bb2847243b2e4', 0)

        self.assertEqual(mock_index.call_count, 12)
        mock_index.assert_any_call(
            'moving-image', [{'foo': 'bar'}, {'baz': 'buz'}], None)
        mock_index.assert_any_call(
            'audio', [{'foo': 'bar'}, {'baz': 'buz'}], None)
        mock_index.assert_any_call(
            'catalogued-reports', [{'foo': 'bar'}, {'baz': 'buz'}], None)
        mock_set_last_fetched.assert_called_once_with(
            ANY, "last_fetched_timestamp.txt")

    def test_get_last_fetched_timestamp(self):
        filepath = "last_export.txt"

        """No timestamp file, should return 0"""
        Path(filepath).unlink(missing_ok=True)
        output = self.updater.get_last_fetched_timestamp(filepath)
        self.assertEqual(output, 0)

        """Correctly read contents of timestamp file"""
        timestamp = 12345
        with open(filepath, "w") as fp:
            fp.write(str(timestamp))
        output = self.updater.get_last_fetched_timestamp(filepath)
        self.assertEqual(output, timestamp)

        """Clean up timestamp file."""
        Path(filepath).unlink()

    def test_set_last_fetched_timestamp(self):
        filepath = "last_export.txt"
        timestamp = 12345

        self.updater.set_last_fetched_timestamp(timestamp, filepath)
        with open(filepath, "r") as fp:
            data = fp.read()
        self.assertEqual(int(data), timestamp)

    def test_get_refids_from_files(self):
        dirpath = getenv("ASSETS_DIR")
        p = Path(dirpath)
        p.mkdir()
        for subdir in ["00455a772f0d2c3dde0bb2847243b2e2",
                       "00455a772f0d2c3dde0bb2847243b2e2a", "z"]:
            (p / subdir).mkdir()

        """Run with no last fetched time"""
        existing, new = self.updater.get_refids_from_files(dirpath, 0)
        self.assertEqual(existing, [])
        self.assertEqual(new, ["00455a772f0d2c3dde0bb2847243b2e2"])

        """Future last fetched time"""
        existing, new = self.updater.get_refids_from_files(
            dirpath, datetime.now().timestamp())
        self.assertEqual(existing, ["00455a772f0d2c3dde0bb2847243b2e2"])
        self.assertEqual(new, [])

    def test_get_updated_data(self):
        mock_get_paged = Mock()
        mock_get_paged.return_value = [{"json": json.dumps({"foo": "bar"})}]
        self.updater.as_client = Mock()
        self.updater.as_client.get_paged = mock_get_paged
        self.updater.as_repo = "2"
        refid_list = [
            "00455a772f0d2c3dde0bb2847243b2e2",
            "00455a772f0d2c3dde0bb2847243b2e3"]

        """No last fetch time"""
        output = self.updater.get_updated_data(refid_list, 0)
        self.assertEqual(output, [{"foo": "bar"}])
        mock_get_paged.assert_called_once_with(
            '/repositories/2/search?q=refid:00455a772f0d2c3dde0bb2847243b2e2 OR 00455a772f0d2c3dde0bb2847243b2e3&type[]=archival_object&fields[]=json&page=1')
        mock_get_paged.reset_mock()

        """With last fetch time"""
        output = self.updater.get_updated_data(refid_list, 1234567)
        self.assertEqual(output, [{"foo": "bar"}])
        mock_get_paged.assert_called_once_with(
            '/repositories/2/search?q=refid:00455a772f0d2c3dde0bb2847243b2e2 OR 00455a772f0d2c3dde0bb2847243b2e3&type[]=archival_object&filter={"query": {"jsonmodel_type": "range_query", "field": "system_mtime", "from": "1970-01-15T06:56:07Z"}}&fields[]=json&page=1')

    def test_generate_docs(self):
        category = "audio"
        to_index = [{
            "ref_id": "1234567",
            "uri": "/repositories/2/archival_objects/1",
            "display_string": "display_string",
            "notes": []}]
        expected = [{
            "_id": "1234567",
            "category": category,
            "dimes_id": "YRa9EbvFzk9qcLdrsEhK6u",
            "url": "/1234567",
            "title": "display_string",
            "notes": []}]
        output = self.updater.generate_docs(category, to_index)
        self.assertEqual(list(output), expected)

    @patch('src.update.streaming_bulk')
    @patch('src.update.Updater.generate_docs')
    def test_index_data(self, mock_docs, mock_streaming_bulk):
        self.updater.es_client = Mock()

        """Test successful index"""
        mock_streaming_bulk.return_value = [(True, "good")]
        self.updater.index_data("audio", [], "default")
        mock_streaming_bulk.assert_called_once_with(
            client=self.updater.es_client,
            index="default", actions=mock_docs())

        """Test indexing error"""
        mock_streaming_bulk.return_value = [(False, "Error indexing data")]
        with self.assertRaises(Exception) as err:
            self.updater.index_data("audio", [], "default")
        self.assertEqual(str(err.exception),
                         "Errors encountered while indexing: Error indexing data")

    def tearDown(self):
        if Path(getenv("ASSETS_DIR")).is_dir():
            rmtree(getenv("ASSETS_DIR"))
