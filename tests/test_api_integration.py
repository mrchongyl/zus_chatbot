import pytest
import requests

def test_products_endpoint():
    resp = requests.get("http://127.0.0.1:8000/products", params={"query": "tumbler"})
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data and len(data["products"]) > 0

def test_outlets_endpoint():
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"query": "Cheras"})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data and len(data["results"]) > 0

def test_products_failure():
    resp = requests.get("http://127.0.0.1:8000/products", params={"query": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert "No products found" in data.get("summary", "") or data.get("total_results", 1) == 0

def test_outlets_failure():
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"query": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert ("results" in data and len(data["results"]) == 0) or "no outlets found" in str(data).lower() or "error" in str(data).lower()
