"""
Main Agentic Chatbot using LangChain Custom ReAct Pattern
==================================================

This chatbot can:
1. Calculate mathematical expressions
2. Find ZUS Coffee outlets using natural language
3. Answer questions about ZUS products using AI search
4. Remember conversation history for multi-turn chats

Architecture:
- Uses Google Gemini 2.0-Flash as the language model
- LangChain ReAct agent with hwchase17/react + custom prompt
- Three main tools: calculator, outlets, products
- Conversation memory for context preservation
"""

import os
import json
import requests
from typing import List
from dotenv import load_dotenv
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.prompts import PromptTemplate

# --- Session and Memory Management ---
# Load API keys
load_dotenv()

# Session-based memory stores for conversation history
session_store = {}

# Get or create a chat message history for a session
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

# Clear the chat history for a session
def clear_session_history(session_id: str):
    if session_id in session_store:
        del session_store[session_id]

# --- LLM and Tool Setup ---
# Setup Gemini for the agent.
def setup_llm():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.3  # 0.1 Low temperature for consistent, factual responses
    )

# Base URL for API requests
API_BASE_URL = "https://zus-chatbot-api-554593173489.asia-southeast1.run.app"

# Base URL for local development:
#API_BASE_URL = "http://127.0.0.1:8000"

# Calculator tool for arithmetic operations.
def calculator_tool(expression: str) -> str:
    """
    Calculator tool for arithmetic operations.    
    Args:
        expression (str): Mathematical expression to evaluate
        
    Returns:
        str: Result of the calculation or error message
        
    Examples:
        calculator_tool("2 + 3") -> "The result of 2 + 3 is 5"
        calculator_tool("(10 * 5) / 2") -> "The result of (10 * 5) / 2 is 25.0"
    """
    try:
        # Make API call to calculator endpoint
        import urllib.parse
        encoded_expression = urllib.parse.quote(expression)
        response = requests.get(
            f"{API_BASE_URL}/calculator?expression={encoded_expression}",
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', 'Error in calculation')
            return f"The result of {expression} is {result}"
        else:
            return f"Calculator API error: {response.status_code}"
    except requests.RequestException as e:
        return f"Failed to connect to calculator API: {str(e)}"
    except Exception as e:
        return f"Error calculating: {expression}"

# Outlets tool for outlet search
def outlets_tool(query: str) -> str:
    """    
    This tool uses Text2SQL conversion with Gemini to translate
    natural language queries into database searches.
    Args:
        query (str): Description of outlets to find
        
    Returns:
        dict: Contains the user query and the full list of matching outlets
    
    Examples:
        outlets_tool("outlets in Kuala Lumpur") -> Returns all KL outlets
        outlets_tool("outlets open until 10 PM") -> Returns outlets with that opening time
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/outlets",
            params={"query": query},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            outlets = data.get('results', [])
            message = data.get('message', '')
            if not outlets:
                return str([{
                    "query": query,
                    "outlets": [],
                    "message": message or f"No outlets found for query: {query}\n"
                }])
            return str([{
                "query": query,
                "outlets": outlets
            }]) + "\n"
        else:
            return str([{
                "query": query,
                "outlets": [],
                "message": f"Outlets API error: {response.status_code}\n"
            }])
    except requests.RequestException as e:
        return str([{
            "query": query,
            "outlets": [],
            "message": f"Failed to connect to outlets API: {str(e)}\n"
        }])
    except Exception as e:
        return str([{
            "query": query,
            "outlets": [],
            "message": f"Error processing outlets request: {str(e)}\n"
        }])

# Products tool for product search and summary
def products_tool(query: str) -> str:
    """
    This tool uses a FAISS vector database to find relevant products
    and then generates an AI summary of the results.
    
    Args:
        query (str): What product information to search for
        
    Returns:
        str: AI-generated summary of relevant products
        
    Examples:
        products_tool("coffee cups") -> Information about coffee cup products
        products_tool("tumblers") -> Details about tumbler products  
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/products?query={query}&top_k=3",
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            # Get AI summary
            summary = data.get('summary', 'No summary available')
            products = data.get('products', [])
            total_results = data.get('total_results', 0)
            if total_results == 0:
                return f"No drinkware products found for: {query}"
            # Format response with AI summary and product details
            result = f"Product Search Results for '{query}':\n\n"
            result += f"[Summary: {summary}]\n\n"
            #result += f"Products ({total_results} found):\n"
            #for i, product in enumerate(products[:3], 1):
            #    result += f"{i}. {product['name']}\n"
            #    result += f"   Price: {product['price']}\n"
            #    result += f"   Promotion: {product['promotion']}\n"
            #    result += f"   Category: {product['category']}\n"
            #    result += f"   Colours: {product['colours']}\n"
            #    result += f"   Similarity Score: {product['similarity_score']:.3f}\n\n"
            return result + "\n"
        else:
            return f"Products API error: {response.status_code}"
    except requests.RequestException as e:
        return f"Failed to connect to products API: {str(e)}"
    except Exception as e:
        return f"Error processing products request: {str(e)}"

# --- Tool List Creation ---
def create_tools() -> List[Tool]:    
    tools = [
        Tool(
            name="Calculator",
            func=calculator_tool,
            description="Useful for performing mathematical calculations. Input should be a mathematical expression like '2+2' or '10*5/2'."
        ),
        Tool(
            name="ZUS_Outlets",
            func=outlets_tool,
            description="Get information about ZUS Coffee outlet locations, directions and operation time. You can search by area/city name (e.g., 'Cheras', 'Kuala Lumpur'), opening hours, or general queries. Examples: 'outlets in Cheras', 'outlets open until 10 PM'.",
        ),
        Tool(
            name="ZUS_Products", 
            func=products_tool,
            description="Search for ZUS Coffee drinkware products like tumblers, mugs, cups, etc. Returns AI-generated product recommendations with details and pricing."
        )
    ]
    return tools

# --- Agent Setup ---
def create_agent():    
    # Setup LLM
    llm = setup_llm()
    # Create tools
    tools = create_tools()
    # Use the official ReAct prompt from LangChain hub
    react_prompt = hub.pull("hwchase17/react")
    custom_instructions = """
    
    You are a helpful, friendly assistant for ZUS Coffee with access to tools that return structured data (e.g., outlets, products, calculations) and reply in a friendly, conversational tone to make the user feel comfortable and engaged, include emoji where appropriate.
    
    Always follow the ReAct format:
    Thought: I need to look up outlets in ss2.
    Action: Outlets
    Action Input:... (e.g.: "outlets in ss2")

    (observe tool output)

    Thought: I now know the final answer.
    Final Answer: ...
        

    IMPORTANT:
    - Never answer before 'Final Answer:'.
    - Think step-by-step about what you need to do.
    - If the question do not require a tool, just provide the answer directly with 'Final Answer'.
    - Use bullet points ("- Item") for lists, each on a new line.
    - Keep track of previous user queries, action input, and final answer to maintain context in multi-turn conversations.
    - For outlet searches, list only outlet names unless the user asks for more (e.g., address, hours, directions).
    - If the user makes a very long, complex, or multi-part request (e.g., asking for products, outlets, and calculations at once, or inputting complex arithmetic), politely refuse and ask them to simplify or split it into smaller parts.
    - If unsure about the detail, ask the user relevant follow-up questions to clarify their intent.
    - When appropriate, offer the user additional details or context to help guide their understanding of the topic.

    """
    # Combine custom instructions with the official ReAct template
    combined_prompt = PromptTemplate(
        input_variables=react_prompt.input_variables,
        template=custom_instructions + react_prompt.template
    )
    # Create the agent
    agent = create_react_agent(llm, tools, combined_prompt)
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=6,
        max_execution_time=60,
        handle_parsing_errors=True
    )
    # Setup for message history
    agent_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
    )
    return agent_with_history

# --- CLI Chat Interface ---
def chat_interface():    
    print("ZUS Coffee Chatbot")
    print("=" * 50)
    print("\nType 'quit' to exit, 'clear' to clear memory")
    print("=" * 50)
    try:
        agent = create_agent()
        session_id = "user_session"  # Using a fixed session ID for command-line interface
        while True:
            user_input = input("\n🙋 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using ZUS Coffee chatbot!")
                break
            if user_input.lower() == 'clear':
                # Clear session history instead of recreating agent
                clear_session_history(session_id)
                print("\nMemory cleared!")
                continue
            if not user_input:
                continue
            # Block direct SQL input
            sql_keywords = ['select', 'insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate']
            if any(user_input.strip().lower().startswith(kw) for kw in sql_keywords):
                print("\nSQL queries are not allowed. Please use natural language.")
                continue
            try:
                print(f"\n🤖 Assistant: ", end="", flush=True)
                response = agent.invoke(
                    {"input": user_input},
                    config={"configurable": {"session_id": session_id}}
                )
                print(response['output'])
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try again with a different question.")
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nFailed to initialize agent: {str(e)}")
        print("Please check that all APIs are running and environment variables are set.")

if __name__ == "__main__":
    chat_interface()
