import os
from config.config import INDEX_NAME_DEFAULT
from connectElasticSearch import get_es_client
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from index_data import update_click_count
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv() 

app = FastAPI()

FRONTEND_URL = os.environ.get("FRONTEND_URL")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

class ClickRequest(BaseModel):
    url: str

class SearchRequest(BaseModel):
    filterQuery: str

STOP_WORDS = set([
    "a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "of", "to", "in", "on", "at", 
    "by", "with", "about", "as", "from", "that", "which", "who", "whom", "whose", "this", "these", 
    "those", "i", "you", "he", "she", "it", "we", "they", "is", "are", "was", "were", "be", "been", 
    "being", "have", "has", "had", "having", "do", "does", "did", "doing"
])

def remove_stop_words(query: str) -> str:
    words = query.split()
    filtered_words = [word for word in words if word.lower() not in STOP_WORDS]
    return " ".join(filtered_words)

@app.get("/api")
async def getAll():
    print(FRONTEND_URL)
    es = get_es_client()
    if not es:
        raise HTTPException(status_code=500, detail="Elasticsearch client initialization failed")
    try:
        response = es.search(
            index=INDEX_NAME_DEFAULT,
            body={
                "query": {
                    "match_all": {}
                },
                "size": 200
            }
        )

        hits = response.get("hits", {}).get("hits", [])

        results = [
            {
                "url": hit["_source"].get("url", ""),
                "favicon": hit["_source"].get("favicon", ""),
                "title": hit["_source"].get("title", ""),
                "headings": hit["_source"].get("headings", ""),
                "content": hit["_source"].get("content", ""),
                "filters": hit["_source"].get("filters", []),
                "score": hit.get("_score", 0),
                "click_count": hit["_source"].get("click_count", 0),
            }
            for hit in hits
        ]

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# api/search
@app.post("/api/search/")
async def search(
    query: str = Query(..., description="Search query text"),
    filter: str = Query(None)
) -> dict:
    filter_query = filter
    clean_query = remove_stop_words(query)

    es = get_es_client()
    if not es:
        raise HTTPException(status_code=500, detail="Elasticsearch client initialization failed")

    try:
        response = es.search(
            index=INDEX_NAME_DEFAULT,
            body={
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "filter": [
                                    {"match": {"filters": filter_query}}
                                ],
                                "should": [
                                    {"match": {"title": clean_query}},
                                    {"match": {"headings": clean_query}}, 
                                    {"match": {"content": clean_query}}
                                ],
                                "minimum_should_match": 1
                            }
                        },
                        "functions": [
                            {"filter": {"match": {"title": clean_query}}, "weight": 5},
                            {"filter": {"match": {"headings": clean_query}}, "weight": 3},
                            {"filter": {"match": {"content": clean_query}}, "weight": 1.5},
                            {"filter": {"term": {"filters.keyword": f"{filter_query}-head"}}, "weight": 10},
                            {"filter": {"term": {"filters.keyword": f"{filter_query}-cont"}}, "weight": 2},
                        ],
                        "score_mode": "sum",
                        "boost_mode": "multiply"
                    }
                },
                "sort": [
                    {"click_count": {"order": "desc", "missing": 0}},
                    {"_score": {"order": "desc"}}
                ],
                "size": 200
            }
        )
        hits = response.get("hits", {}).get("hits", [])

        results = []
        for hit in hits:
            source = hit["_source"]
            title = source.get("title", "")

            headings_str = source.get("headings", "")
            headings_str = headings_str.replace("'", "").replace('"', "").replace("[", "").replace("]", "")
            headings = [heading.strip() for heading in headings_str.split(",")]
            matched_heading = next((heading for heading in headings if clean_query.lower() in heading.lower()), None)
            title_to_use = matched_heading if matched_heading else title

            content_str = source.get("content", "")
            content_str = content_str.replace("'", "").replace('"', "").replace("[", "").replace("]", "")
            content = [content.strip() for content in content_str.split(",")]
            matched_content = next((content_item for content_item in content if clean_query.lower() in content_item.lower()), None)
            content_to_use = matched_content if matched_content else content_str
            if(len(content_to_use) > 200):
                content_to_use = content_to_use[:200] + "..."
            else:
                content_to_use = content_to_use

            result = {
                "url": source.get("url", ""),
                "favicon": source.get("favicon", ""),
                "title": title_to_use,
                "content": content_to_use,
                # "filters": source.get("filters", []),
                # "score": hit.get("_score", 0),
                # "click_count": source.get("click_count", 0),
            }

            results.append(result)

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/click/")
async def click(request: ClickRequest):
    print(f"Received click for URL: {request.url}")
    es = get_es_client()
    
    if not es:
        raise HTTPException(status_code=500, detail="Elasticsearch client initialization failed")

    try:
        update_click_count(es, request.url)
        return {"message": f"Click count updated for URL: {request.url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

