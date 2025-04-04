import os
import time
from pprint import pprint
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
load_dotenv() 

ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")

def get_es_client(max_retries: int = 1, sleep_time: int = 0) -> Elasticsearch:
    i = 0
    while i < max_retries:
        try:
            es = Elasticsearch(ELASTICSEARCH_URL)
            pprint('Connected to Elasticsearch!')
            return es
        except Exception:
            pprint('Could not connect to Elasticsearch, retrying...')
            time.sleep(sleep_time)
            i += 1
    raise ConnectionError("Failed to connect to Elasticsearch after multiple attempts.")


# docker run -p 127.0.0.1:9200:9200 -d --name elasticsearch \
#   -e "discovery.type=single-node" \
#   -e "xpack.security.enabled=false" \
#   -e "xpack.license.self_generated.type=trial" \
#   -v "elasticsearch-data:/usr/share/elasticsearch/data" \
#   docker.elastic.co/elasticsearch/elasticsearch:8.15.0
