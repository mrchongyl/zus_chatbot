import requests
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

UNHAPPY_PHRASES = [
    "error", "invalid", "sorry", "not", "can't calculate", "incomplete", "isn't", "cut off", "too long", "too large", "refuse", "not allowed", "unsafe", "zero", "only", "complex", "didn't", "empty", "unavailable", "timeout", "no product", "not found", "try again", "please"
]

# Calculator Tests
def test_calculator_wrong_param():
    response = requests.get("http://127.0.0.1:8000/calculator", params={"expr": "42+1"})
    assert response.status_code in (400, 422)

def test_calculator_no_param():
    response = requests.get("http://127.0.0.1:8000/calculator")
    assert response.status_code in (400, 422)

def test_calculator_post_method():
    response = requests.post("http://127.0.0.1:8000/calculator", data={"expression": "1+1"})
    assert response.status_code == 405

def test_calculator_special_characters():
    response = requests.get("http://127.0.0.1:8000/calculator", params={"expression": "5+😊"})
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

# Outlets Tests
def test_outlets_post_method():
    response = requests.post("http://127.0.0.1:8000/outlets", data={"query": "KL"})
    assert response.status_code == 405

def test_outlet_empty():
    response = requests.get("http://127.0.0.1:8000/outlets", params={"query": ""})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

def test_outlets_special_characters():
    response = requests.get("http://127.0.0.1:8000/outlets", params={"query": "💥@#*&^%$"})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

def test_outlets_large_query():
    big_query = "KL " * 1000
    response = requests.get("http://127.0.0.1:8000/outlets", params={"query": big_query})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)
    
def test_outlets_wrong_param():
    response = requests.get("http://127.0.0.1:8000/outlets", params={"q": "KL"})
    assert response.status_code in (400, 422)

def test_sql_injection():
    response = requests.get("http://127.0.0.1:8000/outlets", params={"query": "DROP TABLE outlets;"})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

# Products API Tests
def test_products_post_method():
    response = requests.post("http://127.0.0.1:8000/products", data={"query": "tumbler"})
    assert response.status_code == 405
    
def test_products_empty():
    response = requests.get("http://127.0.0.1:8000/products", params={"query": ""})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

def test_products_special_characters():
    response = requests.get("http://127.0.0.1:8000/products", params={"query": "💥@#*&^%$"})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

def test_products_large_query():
    big_query = "tumbler " * 1000
    response = requests.get("http://127.0.0.1:8000/products", params={"query": big_query})
    assert response.status_code == 200
    assert any(phrase in response.text.lower() for phrase in UNHAPPY_PHRASES)

def test_products_wrong_param():
    response = requests.get("http://127.0.0.1:8000/products", params={"q": "tumbler"})
    assert response.status_code in (400, 422)


