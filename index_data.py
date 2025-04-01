from typing import List
from config.config import INDEX_NAME_DEFAULT
from connectElasticSearch import get_es_client
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm
import pandas as pd

def index_data(documents: List[dict], batch_size: int = 500):
    es = get_es_client(max_retries=5, sleep_time=5)
    
    if not es.ping():
        print("Elasticsearch is not reachable. Please check your connection.")
        return
    
    _create_index(es=es)
    _insert_documents(es=es, documents=documents, batch_size=batch_size)
    print(f'Indexed {len(documents)} documents into Elasticsearch index "{INDEX_NAME_DEFAULT}"')

def _create_index(es: Elasticsearch):
    try:
        if es.indices.exists(index=INDEX_NAME_DEFAULT):
            es.indices.delete(index=INDEX_NAME_DEFAULT)
            print(f"Deleted existing index: {INDEX_NAME_DEFAULT}")
        es.indices.create(index=INDEX_NAME_DEFAULT)
        print(f"Created new index: {INDEX_NAME_DEFAULT}")
    except Exception as e:
        print(f"Error creating index: {e}")

def _insert_documents(es: Elasticsearch, documents: List[dict], batch_size: int):
    try:
        for i in tqdm(range(0, len(documents), batch_size), desc='Indexing documents'):
            batch = documents[i:i+batch_size]
            actions = [
                {"_index": INDEX_NAME_DEFAULT, "_source": doc}
                for doc in batch
            ]
            helpers.bulk(es, actions)
        print("All documents indexed successfully.")
    except Exception as e:
        print(f"Error indexing documents: {e}")

def update_click_count(es: Elasticsearch, url: str):
    try:
        if not es.indices.exists(index=INDEX_NAME_DEFAULT):
            print(f"Index {INDEX_NAME_DEFAULT} does not exist.")
            return
        
        query = {
            "script": {
                "source": """
                    if (ctx._source.containsKey('click_count')) { 
                        ctx._source.click_count += 1; 
                    } else { 
                        ctx._source.click_count = 1; 
                    }
                """,
                "lang": "painless"
            },
            "query": {
                "term": {"url.keyword": url}
            }
        }

        response = es.update_by_query(index=INDEX_NAME_DEFAULT, body=query)
        updated_count = response.get('updated', 0)

        if updated_count > 0:
            print(f"Click count updated for URL: {url}")
        else:
            print(f"No document found for URL: {url}")

    except Exception as e:
        print(f"Error updating click count for URL {url}: {e}")


if __name__ == '__main__':
    parquet_file_path = 'data/data.parquet'
    df = pd.read_parquet(parquet_file_path)
    documents = df.to_dict(orient='records')
    
    index_data(documents=documents, batch_size=500)
