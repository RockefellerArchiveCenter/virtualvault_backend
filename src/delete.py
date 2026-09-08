import argparse
import logging
from os import getenv

from elasticsearch import Elasticsearch

logging.basicConfig(level=int(getenv('LOGGING_LEVEL', logging.INFO)))


class Deleter(object):

    def __init__(self):
        self.es_client = Elasticsearch(hosts=[getenv("ES_HOST")])

    def run(self, ref_id):
        """Main method which calls all other submethods."""
        logging.info("Starting delete")
        self.es_client.delete(index=getenv("ES_INDEX"), id=ref_id)
        logging.info("Delete complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'ref_id',
        help='ArchivesSpace ref ID of object to be deleted')
    args = parser.parse_args()
    Deleter().run(args.ref_id)
