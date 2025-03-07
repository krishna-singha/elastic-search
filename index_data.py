import json
import torch
from tqdm import tqdm
from typing import List
from pprint import pprint
from config.config import INDEX_NAME_EMBEDDING
from connectElasticSearch import get_es_client
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

def index_data(documents: List[dict], model: SentenceTransformer) -> None:
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es=es)
    _ = _index_documents(es=es, documents=documents, model=model)
    
    pprint(f'✅ Indexed {len(documents)} documents into Elasticsearch index: {INDEX_NAME_EMBEDDING}')

def _create_index(es: Elasticsearch) -> dict:
    index_name = INDEX_NAME_EMBEDDING
    
    # Delete index if it already exists
    es.indices.delete(index=index_name, ignore_unavailable=True)
    
    # Create new index with proper mappings
    return es.indices.create(
        index=index_name,
        body={
            "mappings": {
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "keywords": {"type": "keyword"},
                    "timestamp": {
                        "type": "date",
                        "format": "yyyy-MM-dd HH:mm:ss"  # ✅ Correct timestamp format
                    },
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
        try:
            # ✅ Encode "content" field for semantic search
            embedding = model.encode(document['content']).tolist()
            
            # ✅ Ensure timestamp is in correct format
            timestamp = document["timestamp"]
            
            # ✅ Store full document + embedding
            operations.append({'index': {'_index': INDEX_NAME_EMBEDDING}})
            operations.append({
                "url": document["url"],
                "title": document["title"],
                "content": document["content"],
                "keywords": document.get("keywords", []),
                "timestamp": timestamp,
                "embedding": embedding
            })
        except Exception as e:
            pprint(f"❌ Error indexing document {document['url']}: {str(e)}")
    
    return es.bulk(body=operations)  # ✅ Bulk indexing for speed

if __name__ == '__main__':
    with open('data/data.json') as f:
        documents = json.load(f)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # ✅ Use GPU if available
    model = SentenceTransformer('all-MiniLM-L6-v2').to(device)
    
    index_data(documents=documents, model=model)
