import requests
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

UNHAPPY_PHRASES = [
    "error", "invalid", "sorry", "not", "can't calculate", "incomplete", "isn't", "cut off", "too long", "too large", "refuse", "not allowed", "unsafe", "zero", "only", "complex", "didn't", "empty", "unavailable", "timeout", "no product", "not found"
]

def test_calculator_wrong_param():
    resp = requests.get("http://127.0.0.1:8000/calculator", params={"expr": "42+1"})
    assert resp.status_code in (400, 422)

def test_calculator_no_param():
    resp = requests.get("http://127.0.0.1:8000/calculator")
    assert resp.status_code in (400, 422)

def test_calculator_post_method():
    resp = requests.post("http://127.0.0.1:8000/calculator", data={"expression": "1+1"})
    assert resp.status_code == 405

def test_outlets_post_method():
    resp = requests.post("http://127.0.0.1:8000/outlets", data={"query": "KL"})
    assert resp.status_code == 405

def test_outlets_special_characters():
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"query": "💥@#*&^%$"})
    print("Response text:", resp.text)  # Add this line
    assert resp.status_code == 200
    assert any(phrase in resp.text.lower() for phrase in UNHAPPY_PHRASES)

def test_outlets_large_query():
    big_query = "KL " * 1000
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"query": big_query})
    print("Response text:", resp.text)  # Add this line
    assert resp.status_code == 200
    assert any(phrase in resp.text.lower() for phrase in UNHAPPY_PHRASES)

def test_products_tool_empty(monkeypatch):
    from chatbot.main_agent import products_tool
    monkeypatch.setattr("chatbot.main_agent.products_tool", lambda q: "")
    print("Response text:", resp.text)  # Add this line
    result = products_tool("")
    assert any(phrase in result.lower() for phrase in UNHAPPY_PHRASES)

def test_products_tool_special_characters():
    from chatbot.main_agent import products_tool
    result = products_tool("💥@#*&^%$")
    assert any(phrase in result.lower() for phrase in UNHAPPY_PHRASES)

def test_products_tool_large_query():
    from chatbot.main_agent import products_tool
    big_query = "tumbler " * 1000
    result = products_tool(big_query)
    assert any(phrase in result.lower() for phrase in UNHAPPY_PHRASES)

def test_outlets_wrong_param():
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"q": "KL"})
    assert resp.status_code in (400, 422)
