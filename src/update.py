import json
import logging
from datetime import datetime
from os import getenv
from pathlib import Path

from asnake.aspace import ASpace
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from shortuuid import uuid

logging.basicConfig(level=int(getenv('LOGGING_LEVEL', logging.INFO)))


class Updater(object):

    def __init__(self):
        self.as_client = ASpace(
            baseurl=getenv("AS_BASEURL"),
            username=getenv("AS_USERNAME"),
            password=getenv("AS_PASSWORD")).client
        self.as_repo = getenv("AS_REPO")
        self.es_client = Elasticsearch(hosts=[getenv("ES_HOST")])

    def run(self):
        """Main method which calls all other submethods.

        This logic simultaneously handles two cases: indexing updated metadata for existing
        items and also indexing metadata for new items.
        """
        logging.info("Starting fetch")
        start_time = int(datetime.now().timestamp())
        last_fetched = self.get_last_fetched_timestamp(
            getenv("LAST_FETCHED_FILEPATH"))
        for category_dir in Path(getenv("ASSETS_DIR")).iterdir():
            if category_dir.is_dir():
                existing_refid_list, new_refid_list = self.get_refids_from_files(
                    category_dir, last_fetched)
                for refid_list, refid_last_fetched in [
                        (existing_refid_list, last_fetched), (new_refid_list, 0)]:
                    for chunk in self.list_chunks(refid_list):
                        to_index = self.get_updated_data(
                            chunk, refid_last_fetched)
                        self.index_data(
                            category_dir.stem, to_index, getenv("ES_INDEX"))
        self.set_last_fetched_timestamp(
            start_time, getenv("LAST_FETCHED_FILEPATH"))
        logging.info("Fetch complete")

    def get_last_fetched_timestamp(self, filepath):
        """Reads last fetched timestamp from file."""
        try:
            with open(filepath, "r") as fp:
                last_fetched = int(fp.read())
        except FileNotFoundError:
            last_fetched = 0
        logging.debug(f"Last fetched time: {last_fetched}")
        return last_fetched

    def set_last_fetched_timestamp(self, timestamp, filepath):
        """Writes last fetched timestamp to file."""
        with open(filepath, "w") as fp:
            fp.write(str(timestamp))
        logging.debug(f"Last fetched time of {timestamp} stored")

    def get_refids_from_files(self, dirpath, last_export):
        """Iterate through list of directories to create list of refids"""
        base_dir = Path(dirpath)
        refids = []
        new_refids = []
        if base_dir.is_dir():
            for fp in base_dir.iterdir():
                if fp.is_dir() and len(fp.name) == 32:
                    created_time = fp.stat().st_ctime
                    if created_time >= last_export:
                        new_refids.append(fp.name)
                    else:
                        refids.append(fp.name)
        logging.debug(
            f"Found {
                len(refids)} existing refids and {
                len(new_refids)} new refids in {dirpath}")
        return refids, new_refids

    def list_chunks(self, lst, n=int(getenv('AS_CHUNK_SIZE'))):
        """Divide a list up into chunks"""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def get_updated_data(self, refid_list, last_fetch):
        """Fetch updated data from ArchivesSpace.

        If a last_fetch timestamp is provided, fetches only data updated since that time.
        Otherwise, fetches data for all requested refids.
        """
        refid_value = " OR ".join(refid_list)
        if last_fetch:
            logging.debug(
                f"Fetching data about refids modified since {last_fetch}")
            last_fetch_datetime = datetime.fromtimestamp(last_fetch)
            last_fetch_datestring = last_fetch_datetime.strftime(
                '%Y-%m-%dT%H:%M:%SZ')
            query = json.dumps(
                {
                    "query": {
                        "jsonmodel_type": "range_query",
                        "field": "system_mtime",
                        "from": last_fetch_datestring}})
            url = f'/repositories/{
                self.as_repo}/search?q=refid:{refid_value}&filter={query}&fields[]=json&page=1'
        else:
            logging.debug("Fetching data about refids")
            url = f'/repositories/{
                self.as_repo}/search?q=refid:{refid_value}&fields[]=json&page=1'
        resp = self.as_client.get_paged(url)
        return [json.loads(r['json']) for r in resp]

    def generate_docs(self, category, to_index):
        """Formats data for indexing"""
        for obj in to_index:
            yield {
                "_id": obj["ref_id"],
                "category": category,
                "dimes_id": uuid(name=obj["uri"]),
                "url": f"/{obj['ref_id']}",
                "title": obj['display_string'],
                "notes": obj['notes'],
            }

    def index_data(self, category, to_index, index):
        """Indexes data in Elasticsearch"""
        errors = []
        for ok, item in streaming_bulk(
                client=self.es_client,
                index=index,
                actions=self.generate_docs(category, to_index)):
            if not ok:
                errors.append(item)
        if len(errors):
            raise Exception(
                f"Errors encountered while indexing: {
                    ' '.join(errors)}")
        logging.debug("Data indexed")


if __name__ == "__main__":
    Updater().run()
