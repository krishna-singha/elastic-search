import time

from pprint import pprint
from elasticsearch import Elasticsearch


def get_es_client(max_retries: int = 1, sleep_time: int = 0) -> Elasticsearch:
    i = 0
    while i < max_retries:
        try:
            es = Elasticsearch('http://localhost:9200')
            pprint('Connected to Elasticsearch!')
            return es
        except Exception:
            pprint('Could not connect to Elasticsearch, retrying...')
            time.sleep(sleep_time)
            i += 1
    raise ConnectionError("Failed to connect to Elasticsearch after multiple attempts.")