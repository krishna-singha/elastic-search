import json
import torch
from tqdm import tqdm
from typing import List
from pprint import pprint
from elasticsearch import Elasticsearch
from config import INDEX_NAME_EMBEDDING
from utils import get_es_client
from sentence_transformers import SentenceTransformer

def index_data(documents: List[dict], model: SentenceTransformer) -> None:
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es=es)
    _ = _index_documents(es=es, documents=documents, model=model)
    
    pprint(f'Indexed {len(documents)} documents into Elasticsearch index {INDEX_NAME_EMBEDDING}')
    
def _create_index(es: Elasticsearch) -> dict:
    index_name = INDEX_NAME_EMBEDDING
    
    _ = es.indices.delete(index=index_name, ignore_unavailable=True)
    return es.indices.create(
        index=index_name,
        body={  # ✅ Fix: Correct mapping structure
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384  # ✅ Define embedding dimensions
                    }
                }
            }
        }
    )

def _index_documents(es: Elasticsearch, documents: List[dict], model: SentenceTransformer) -> dict:
    operations = []
    for document in tqdm(documents, total=len(documents), desc='Indexing documents'):
        embedding = model.encode(document['explanation']).tolist()  # ✅ Convert tensor to list
        operations.append({'index': {'_index': INDEX_NAME_EMBEDDING}})
        operations.append({**document, "embedding": embedding})  # ✅ Fix incorrect dict unpacking
    
    return es.bulk(body=operations)  # ✅ Fix: Use `body=operations`

if __name__ == '__main__':
    with open('data/apod.json') as f:
        documents = json.load(f)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # ✅ Fix: Use `device`
    model = SentenceTransformer('all-MiniLM-L6-v2').to(device)
    
    index_data(documents=documents, model=model)
