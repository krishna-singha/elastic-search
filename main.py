from fastapi import FastAPI
# from config.config import INDEX_NAME_N_GRAM, INDEX_NAME_EMBEDDING
from indexing.connectElasticSearch import get_es_client
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
# from models.models import SENTENCE_EMBEDDING_MODEL

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return "<h1>APoD Search Engine</h1>"

# @app.get("/search/{query}")
# def search(query: str):
#     es = get_es_client()
#     res = es.search(index=INDEX_NAME_N_GRAM, body={
#         "query": {
#             "match": {
#                 "text": query
#             }
#         }
#     })
#     return res['hits']['hits']
