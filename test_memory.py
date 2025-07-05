#!/usr/bin/env python3

"""Test the memory functionality of the chatbot agent"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.main_agent import create_agent

def test_memory():
    """Test multi-turn conversation memory"""
    print("🧪 Testing agent memory functionality...")
    
    # Create agent
    agent = create_agent()
    
    # First turn - ask for a calculation
    print("\n=== First Turn ===")
    response1 = agent.invoke({"input": "What is 5 + 3?"})
    print(f"Agent response: {response1['output']}")
    
    # Second turn - refer to previous result
    print("\n=== Second Turn ===")
    response2 = agent.invoke({"input": "What's that result divided by 2?"})
    print(f"Agent response: {response2['output']}")
    
    # Third turn - another follow-up
    print("\n=== Third Turn ===")
    response3 = agent.invoke({"input": "Now multiply that by 10"})
    print(f"Agent response: {response3['output']}")
    
    print("\n✅ Memory test completed!")

if __name__ == "__main__":
    test_memory()
