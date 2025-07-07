import requests
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_missing_parameters():
    # Calculator with no expression
    resp = requests.get("http://127.0.0.1:8000/calculator", params={"expression": ""})
    assert resp.status_code == 200
    output = resp.text.lower()
    assert any(
        phrase in output
        for phrase in [
            "error",
            "invalid",
            "sorry",
            "not",
            "can't calculate"
        ]
    )

    # Outlets with no query
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"query": ""})
    assert resp.status_code == 200
    output = resp.text.lower()
    assert any(
        phrase in output
        for phrase in [
            "no outlets found",
            "error",
            "please specify a location"
        ]
    )

def test_api_downtime(monkeypatch):
    # Simulate HTTP 500 for products
    def fake_get(*args, **kwargs):
        class FakeResp:
            status_code = 500
            def json(self): return {}
            text = "Internal Server Error"
        return FakeResp()
    import requests as real_requests
    monkeypatch.setattr(real_requests, "get", fake_get)
    from chatbot.main_agent import products_tool
    result = products_tool("tumbler")
    assert "error" in result.lower() or "failed" in result.lower()

def test_sql_injection():
    # Try SQL injection in outlets
    resp = requests.get("http://127.0.0.1:8000/outlets", params={"query": "1; DROP TABLE outlets;"})
    assert resp.status_code == 200
    assert any(
        phrase in resp.text.lower()
        for phrase in [
            "invalid",
            "no outlets found"
        ]
    )

def test_products_tool_timeout(monkeypatch):
    from chatbot.main_agent import products_tool

    def slow_products_tool(query):
        time.sleep(5)  # Simulate a long delay
        raise TimeoutError("Simulated timeout")

    monkeypatch.setattr("chatbot.main_agent.products_tool", slow_products_tool)
    try:
        result = products_tool("tumbler")
    except Exception as e:
        assert "timeout" in str(e).lower() or "error" in str(e).lower()

def test_product_not_found():
    from chatbot.main_agent import products_tool
    result = products_tool("unicorn frappuccino")
    assert "not found" in result.lower() or "no product" in result.lower() or "sorry" in result.lower()

def test_calculator_special_characters():
    resp = requests.get("http://127.0.0.1:8000/calculator", params={"expression": "5 + 😊"})
    assert resp.status_code == 200
    assert "error" in resp.text.lower() or "invalid" in resp.text.lower() or "sorry" in resp.text.lower()
