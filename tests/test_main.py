import sys
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from main import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def mock_elasticsearch():
    """Fixture to mock Elasticsearch client."""
    with patch("connectElasticSearch.get_es_client") as mock_es:
        yield mock_es

def test_get_all_documents(mock_elasticsearch):
    mock_elasticsearch.return_value.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "url": "https://example.com",
                        "favicon": "https://example.com/favicon.ico",
                        "title": "Example Title",
                        "headings": "Example Heading",
                        "content": "Example Content",
                        "filters": ["example"],
                        "click_count": 5,
                    },
                    "_score": 1.2
                }
            ]
        }
    }

    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0
    assert data["results"][0]["url"] == "https://www.iitkgp.ac.in"

def test_search_with_query_and_filter(mock_elasticsearch):
    mock_elasticsearch.return_value.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "url": "https://example.com",
                        "favicon": "https://example.com/favicon.ico",
                        "title": "Example Title",
                        "headings": "Example Heading",
                        "content": "Example Content",
                    },
                    "_score": 1.5
                }
            ]
        }
    }

    response = client.post("/api/search/?query=example&filter=all")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert data["results"][0]["title"] == "Prof. Sudip Misra of the Computer Science and Engineering Department sets an inspiring example by winning the Careers360 Outstanding Faculty Award in Computer Science for 2018"

def test_search_with_stop_words_only():
    response = client.post("/api/search/?query=the and of&filter=test")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)

def test_click_endpoint(mock_elasticsearch):
    mock_elasticsearch.return_value.update.return_value = {"result": "updated"}

    response = client.post("/api/click/", json={"url": "https://example.com"})
    assert response.status_code == 200
    assert "message" in response.json()
    assert "https://example.com" in response.json()["message"]
