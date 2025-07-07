import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from chatbot.main_agent import create_agent, clear_session_history

def test_sequential_conversation():
    agent = create_agent()
    session_id = "test_seq"
    clear_session_history(session_id)

    # 1. User asks about outlets in Petaling Jaya
    resp1 = agent.invoke({"input": "Is there an outlet in Petaling Jaya?"}, config={"configurable": {"session_id": session_id}})
    assert "outlet" in resp1["output"].lower() or "yes" in resp1["output"].lower()

    # 2. User follows up about a specific outlet in PJ
    resp2 = agent.invoke({"input": "What about SS 2?"}, config={"configurable": {"session_id": session_id}})
    assert "ss 2" in resp2["output"].lower() or "outlet" in resp2["output"].lower()

    # 3. User asks for the opening time of that outlet
    resp3 = agent.invoke({"input": "What time does it open?"}, config={"configurable": {"session_id": session_id}})
    assert ("open" in resp3["output"].lower() or "time" in resp3["output"].lower()) and ("ss 2" in resp3["output"].lower() or "outlet" in resp3["output"].lower())

    # 4. User changes topic to products
    resp4 = agent.invoke({"input": "Show me tumblers"}, config={"configurable": {"session_id": session_id}})
    assert "tumbler" in resp4["output"].lower()

    # 5. User asks for certain product
    resp5 = agent.invoke({"input": "Do you have pink one?"}, config={"configurable": {"session_id": session_id}})
    assert ("pink" in resp5["output"].lower() or "price" in resp5["output"].lower() or "rm" in resp5["output"].lower())

    # 6. User asks for a product discount
    resp6 = agent.invoke({"input": "Do you have them on discount?"}, config={"configurable": {"session_id": session_id}})
    assert ("RM" in resp6["output"].lower() or "price" in resp6["output"].lower() or "rm" in resp6["output"].lower())

    # 7. User asks for a product price
    resp7 = agent.invoke({"input": "How much if i buy 2 of them?"}, config={"configurable": {"session_id": session_id}})
    assert ("RM" in resp7["output"].lower() or "price" in resp7["output"].lower() or "rm" in resp7["output"].lower())

    clear_session_history(session_id)
