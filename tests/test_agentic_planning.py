import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from chatbot.main_agent import create_agent, clear_session_history
import time

def test_agentic_outlet_variations():
    agent = create_agent()
    session_id = "test_plan_outlet"
    clear_session_history(session_id)

    # Direct area
    response = agent.invoke({"input": "Outlets in SS2"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response["output"].lower() for word in ["zus", "where", "area", "outlet"])
    time.sleep(4)

    # Synonym/alternative phrasing
    response = agent.invoke({"input": "Is there a ZUS Coffee branch at SS2?"}, config={"configurable": {"session_id": session_id}})
    assert "ss2" in response["output"].lower() or "outlet" in response["output"].lower()
    time.sleep(4)

    # Abbreviation
    response = agent.invoke({"input": "Any ZUS in PJ?"}, config={"configurable": {"session_id": session_id}})
    assert "pj" in response["output"].lower() or "petaling jaya" in response["output"].lower()
    time.sleep(4)

    clear_session_history(session_id)

def test_agentic_product_variations():
    agent = create_agent()
    session_id = "test_plan_product"
    clear_session_history(session_id)

    # Direct product
    response = agent.invoke({"input": "Show me blue mugs"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response["output"].lower() for word in ["mug", "mugs", "cup", "tumbler"])
    time.sleep(4)

    # Synonym/alternative phrasing
    response = agent.invoke({"input": "Do you have any blue-colored cups?"}, config={"configurable": {"session_id": session_id}})
    assert "blue" in response["output"].lower() and ("cup" in response["output"].lower() or "mug" in response["output"].lower())
    time.sleep(4)

    # Non-existent product
    response = agent.invoke({"input": "Show me unicorn frappuccino"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response["output"].lower() for word in ["not found", "no product", "sorry", "unavailable", "don't have"])
    time.sleep(4)

    clear_session_history(session_id)

def test_agentic_calculator_variations():
    agent = create_agent()
    session_id = "test_plan_calc"
    clear_session_history(session_id)

    # Direct calculation
    response = agent.invoke({"input": "What is 7*8?"}, config={"configurable": {"session_id": session_id}})
    assert "56" in response["output"]
    time.sleep(4)

    # Natural language
    response = agent.invoke({"input": "Can you add 20 and 17 for me?"}, config={"configurable": {"session_id": session_id}})
    assert "37" in response["output"]
    time.sleep(4)

    # Edge: division by zero
    response = agent.invoke({"input": "What is 1 divided by 0?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response["output"].lower() for word in ["zero", "error", "invalid", "sorry", "can't calculate",  "division"])
    time.sleep(4)

    clear_session_history(session_id)

def test_agentic_edge_cases():
    agent = create_agent()
    session_id = "test_plan_edge"
    clear_session_history(session_id)

    # Ambiguous query
    response = agent.invoke({"input": "Tell me about ZUS"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response["output"].lower() for word in ["outlet", "product", "coffee", "zus"])
    time.sleep(4)

    # Very long/complex query (might fail during the test, but will be blocked by the agent logic can check for final answer in terminal)
    long_query = "Tell me the price of every product and outlet in Kuala Lumpur and calculate 10*10*10*10*10*10*10*10*10*10"
    response = agent.invoke({"input": long_query}, config={"configurable": {"session_id": session_id}})
    assert any(word in response["output"].lower() for word in ["error", "too long", "sorry", "not", "can't calculate", "incomplete", "refuse", "limit", "break down". "please"])
    time.sleep(4)

    clear_session_history(session_id)
