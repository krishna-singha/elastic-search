from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from queue import Queue
import threading
from spider import Spider
from general import file_to_set
from domain import get_domain_name
from database import get_collection  # ✅ Import MongoDB connection

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project details
PROJECT_NAME = "navX"
NUMBER_OF_THREADS = 8
queue = Queue()

# Pydantic Model for input validation
class CrawlRequest(BaseModel):
    url: str

# Worker threads
def create_workers(spider_instance):
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work, args=(spider_instance,))
        t.daemon = True
        t.start()

# Crawl function
def work(spider_instance):
    while True:
        url = queue.get()
        if url is None:
            break  # Stop worker if None is received
        try:
            print(f"Crawling: {url}")
            page_title = spider_instance.crawl_page(threading.current_thread().name, url)  # Get page title
            save_to_db(url, page_title)  # ✅ Save to MongoDB
        except Exception as e:
            print(f"Error crawling {url}: {e}")
        queue.task_done()

# Add jobs to queue
def create_jobs(spider_instance):
    links = file_to_set(spider_instance.queue_file)
    for link in links:
        queue.put(link)
    queue.join()

# Save crawled data to MongoDB
def save_to_db(url, title):
    collection = get_collection("crawled_data")  # ✅ Get MongoDB collection
    existing = collection.find_one({"url": url})

    if not existing:
        collection.insert_one({"url": url, "title": title})  # ✅ Store data
        print(f"Saved {url} to DB")
    else:
        print(f"Already exists: {url}")

# Start crawling process
def start_crawling(url: str):
    domain_name = get_domain_name(url)
    spider_instance = Spider(PROJECT_NAME, url, domain_name)  # Create instance of Spider

    create_workers(spider_instance)  # Start workers
    create_jobs(spider_instance)  # Add jobs

    # Stop workers by sending None
    for _ in range(NUMBER_OF_THREADS):
        queue.put(None)

# ✅ Updated /crawl/ API: Saves URL to DB and starts crawling
@app.post("/crawl/")
async def crawl_api(request: CrawlRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(start_crawling, request.url)
    
    # ✅ Save the URL immediately so it appears in search results
    save_to_db(request.url, "Crawling in progress...")

    return {"message": f"Crawling started for {request.url}"}

# ✅ Search API to retrieve crawled results
@app.get("/search/")
async def search_api(query: str):
    collection = get_collection("crawled_data")
    results = list(collection.find({"url": {"$regex": query, "$options": "i"}}, {"_id": 0}))

    return results
