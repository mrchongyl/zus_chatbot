import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from chatbot.main_agent import create_agent, clear_session_history
import time

FAILURE_PHRASES = [
    "error",
    "invalid",
    "sorry",
    "not",
    "can't calculate",
    "incomplete",
    "isn't",
    "cut off",
    "too long",
    "too large",
    "refuse",
    "not allowed",
    "unsafe",
    "zero",
    "only",
    "complex",
    "didn't",
    "empty"
]

def test_calculator_basic_operations():
    agent = create_agent()
    session_id = "test_calc_basic"
    clear_session_history(session_id)

    # Addition
    response = agent.invoke({"input": "Calculate 20 + 17"}, config={"configurable": {"session_id": session_id}})
    assert "37" in response["output"]
    time.sleep(4)

    # Subtraction
    response = agent.invoke({"input": "Calculate 50 - 13"}, config={"configurable": {"session_id": session_id}})
    assert "37" in response["output"]
    time.sleep(4)

    # Multiplication
    response = agent.invoke({"input": "Calculate 37 * 1"}, config={"configurable": {"session_id": session_id}})
    assert "37" in response["output"] or "37.0" in response["output"]
    time.sleep(4)

    # Division
    response = agent.invoke({"input": "Calculate 74 / 2"}, config={"configurable": {"session_id": session_id}})
    assert "37" in response["output"] or "37.0" in response["output"]
    time.sleep(4)

    # Percentage
    response = agent.invoke({"input": "Calculate 37% of 100"}, config={"configurable": {"session_id": session_id}})
    assert "37" in response["output"] or "37.0" in response["output"]
    time.sleep(4)

    clear_session_history(session_id)

def test_calculator_failures():
    agent = create_agent()
    session_id = "test_calc_fail"
    clear_session_history(session_id)

    # Invalid input: text
    response = agent.invoke({"input": "Calculate apple + orange"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    # Empty input
    response = agent.invoke({"input": "Calculate "}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    # Nonsense input
    response = agent.invoke({"input": "Calculate 2 +"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    clear_session_history(session_id)

def test_calculator_hacking_attempts():
    agent = create_agent()
    session_id = "test_calc_hack"
    clear_session_history(session_id)

    # Attempt code injection
    response = agent.invoke({"input": "Calculate __import__('os').system('echo hacked')"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    # Attempt to access builtins
    response = agent.invoke({"input": "Calculate __builtins__"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    clear_session_history(session_id)

def test_calculator_extreme_inputs():
    agent = create_agent()
    session_id = "test_calc_extreme"
    clear_session_history(session_id)

    # Very long expression (complex, not just repeated sums)
    long_expr = "5+23+4*534*12/45+65*55+" * 100 + "7"
    response = agent.invoke({"input": f"Calculate {long_expr}"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    # Very large number
    response = agent.invoke({"input": "Calculate 10**1000"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    # Division by zero
    response = agent.invoke({"input": "Calculate 1 / 0"}, config={"configurable": {"session_id": session_id}})
    output = response["output"].lower()
    assert any(phrase in output for phrase in FAILURE_PHRASES)
    time.sleep(4)

    clear_session_history
    (session_id)
