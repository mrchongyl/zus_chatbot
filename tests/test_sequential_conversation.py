import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import time
from chatbot.main_agent import create_agent, clear_session_history

def test_sequential_conversation():
    agent = create_agent()
    session_id = "test_seq"
    clear_session_history(session_id)

    # 1. User asks about outlets in Petaling Jaya
    response1 = agent.invoke({"input": "Is there an outlet in Petaling Jaya?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response1["output"].lower() for word in ["ss2", "outlet", "yes"])
    time.sleep(5)

    # 2. User follows up about a specific outlet in PJ
    response2 = agent.invoke({"input": "What about SS2?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response2["output"].lower() for word in ["ss2", "yes"])
    time.sleep(5)

    # 3. User asks for the opening time of that outlet
    response3 = agent.invoke({"input": "What time does it open?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response3["output"].lower() for word in ["ss2", "open", "close", "time"])
    time.sleep(5)

    # 4. User changes topic to products
    response4 = agent.invoke({"input": "Show me tumblers"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response4["output"].lower() for word in ["tumbler"])
    time.sleep(5)

    # 5. User asks for certain product
    response5 = agent.invoke({"input": "Do you have pink one?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response5["output"].lower() for word in ["tumbler", "pink", "rm"])
    time.sleep(5)

    # 6. User asks for a product discount
    response6 = agent.invoke({"input": "Do you have them on discount?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response6["output"].lower() for word in ["tumbler", "rm", "sale", "yes"])
    time.sleep(5)

    # 7. User asks for a product price
    response7 = agent.invoke({"input": "How much if i buy 2 of them?"}, config={"configurable": {"session_id": session_id}})
    assert any(word in response7["output"].lower() for word in ["price", "sale", "rm", "yes", "discount"])
    time.sleep(5)

    clear_session_history(session_id)
