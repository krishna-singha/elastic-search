from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sentence_transformers import SentenceTransformer
import torch
from config.config import INDEX_NAME_EMBEDDING
from connectElasticSearch import get_es_client

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Load embedding model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SentenceTransformer('all-MiniLM-L6-v2').to(device)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return "<h1>📚 IIT KGP Search Engine</h1>"

@app.get("/search/all")
def search_all():
    es = get_es_client()
    res = es.search(
        index=INDEX_NAME_EMBEDDING,
        body={
            "query": {
                "match_all": {}
            }
        },
        size=500
    )
    return res["hits"]["hits"]

# 🔍 **Text-Based Search (Exact Match)**
@app.get("/search/text")
def search_text(query: str = Query(..., description="Search query text")):
    es = get_es_client()
    query = query.strip().lower()
    res = es.search(
        index=INDEX_NAME_EMBEDDING,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "title", "keywords"]
                }
            }
        },
        size=100
    )
    
    # Extract relevant results
    results = [
        {
            "url": hit["_source"]["url"],
            "title": hit["_source"]["title"],
            "content": hit["_source"]["content"],
            "keywords": hit["_source"].get("keywords", []),
            "timestamp": hit["_source"]["timestamp"],
            "score": hit["_score"]
        }
        for hit in res["hits"]["hits"]
    ]
    
    return {"query": query, "results": results}

# 🤖 **Semantic Search (Embedding-Based)**
@app.get("/search/semantic")
def search_semantic(query: str = Query(..., description="Search query for semantic understanding")):
    es = get_es_client()
    query = query.strip().lower()
    
    # Convert query to embedding
    query_embedding = model.encode(query).tolist()
    
    res = es.search(
        index=INDEX_NAME_EMBEDDING,
        body={
            "size": 50,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            },
            "min_score": 1.24
        }
    )
    
    # Extract relevant results
    results = [
        {
            "url": hit["_source"]["url"],
            "title": hit["_source"]["title"],
            "content": hit["_source"]["content"],
            "keywords": hit["_source"].get("keywords", []),
            "timestamp": hit["_source"]["timestamp"],
            "score": hit["_score"]
        }
        for hit in res["hits"]["hits"]
    ]
    
    return {"query": query, "results": results}
