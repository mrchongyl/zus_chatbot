"""
ZUS Coffee Chatbot - Streamlit Interface
==========================================

A modern, interactive chatbot interface for the ZUS Coffee system.

Features:
- Clean, modern UI with ZUS Coffee branding
- Real-time conversation with AI agent
- Tool usage visualization (calculator, outlets, products)
- Conversation history and memory
- Loading states and error handling
- Responsive design

Usage:
    streamlit run zus_chatbot.py
"""

import streamlit as st
import sys
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

# Import chatbot
try:
    from chatbot.main_agent import create_agent
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Page configuration
st.set_page_config(
    page_title="ZUS Coffee Assistant",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Intialize streamlit session
def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "agent_initialized" not in st.session_state:
        st.session_state.agent_initialized = False
    
    if "conversation_count" not in st.session_state:
        st.session_state.conversation_count = 0
    
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

def initialize_agent():
    """Initialize agent."""
    if not AGENT_AVAILABLE:
        return False, f"Agent not available: {IMPORT_ERROR}"
    
    try:
        if st.session_state.agent is None:
            with st.spinner("Initializing..."):
                st.session_state.agent = create_agent()
                st.session_state.agent_initialized = True
        return True, "Agent ready"
    except Exception as e:
        return False, f"Failed to initialize agent: {str(e)}"

def display_header():
    """Display the main header."""
    st.title("☕ ZUS Coffee Assistant")
    st.markdown("Your intelligent companion for calculations, outlet locations, and product recommendations")

def display_sidebar():
    """Display the sidebar with features and controls."""
    with st.sidebar:
        
         # Example queries
        st.markdown("## 💡 Try These")
        
        example_queries = [
            "What is 25 * 4?",
            "Find outlets in Kuala Lumpur",
            "Show me travel mugs",
            "Calculate 15% tip on RM45",
            "What's the opening time for ZUS 1 Utama?"
        ]
        
        for query in example_queries:
            if st.button(f"💬 {query}", use_container_width=True, key=f"example_{query}"):
                st.session_state.user_input = query
                st.rerun()

        st.markdown("---")

        # Conversation controls
        st.markdown("## 🎛️ Controls")
        
        if st.button("🔄 Clear Chat", use_container_width=True):
            # Reset agent and conversation state
            st.session_state.agent = None
            st.session_state.agent_initialized = False
            st.session_state.messages = []
            st.session_state.conversation_count = 0
            # Generate a new session_id to fully reset agent memory
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
            # Optionally clear session history from backend if supported
            try:
                from chatbot.main_agent import clear_session_history
                clear_session_history(st.session_state.session_id)
            except ImportError:
                pass
            st.rerun()
        

def display_message(role: str, content: str, **kwargs):
    """Display a chat message with proper line breaks."""
    content_html = content.replace("\n", "<br>")
    st.chat_message(role).markdown(content_html, unsafe_allow_html=True)

def extract_tool_info(response: Dict[str, Any]) -> Optional[Dict]:
    """Extract tool usage information from agent response."""
    try:
        # Look for intermediate steps that show tool usage
        if 'intermediate_steps' in response:
            steps = response['intermediate_steps']
            if steps:
                # Get the last tool used
                last_step = steps[-1]
                if hasattr(last_step, 'tool') and hasattr(last_step, 'tool_input'):
                    return {
                        'name': last_step.tool,
                        'input': str(last_step.tool_input)
                    }
        return None
    except:
        return None

def process_user_input(user_input: str):
    """Process user input and get response."""
    if not user_input.strip():
        return

    # Input length check
    MAX_INPUT_LENGTH = 200
    if len(user_input) > MAX_INPUT_LENGTH:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Your message is too long (>{MAX_INPUT_LENGTH} characters). Please shorten your input.",
            "error": True
        })
        return

    # Block direct SQL input
    sql_keywords = ['select', 'insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate']
    pattern = re.compile(r'\b(' + '|'.join(sql_keywords) + r')\b', re.IGNORECASE)
    if pattern.search(user_input) or ';' in user_input or '*' in user_input:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "SQL queries are not allowed. Please use natural language.",
            "error": True
        })
        return

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Initialize agent if needed
    if not st.session_state.agent_initialized:
        success, message = initialize_agent()
        if not success:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"Error: {message}",
                "error": True
            })
            return
    
    try:
        # Get agent response with session ID
        with st.spinner("🧠 Processing..."):
            # Use a unique session ID for this Streamlit session
            session_id = st.session_state.get('session_id', 'streamlit_default')
            
            response = st.session_state.agent.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            output = response.get('output', 'No response generated')
            
            # Handle parsing errors in the output
            if "Invalid Format" in output or "Missing 'Action:'" in output:
                output = "Sorry, I've encountered a formatting issue. Let me try to help you anyway. What specific information are you looking for about ZUS Coffee?"
            
            # Extract tool information
            tool_info = extract_tool_info(response)
            
            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": output,
                "tool_info": tool_info
            })
            
            st.session_state.conversation_count += 1
    
    except Exception as e:
        # error_msg = ("Sorry, we are currently at capacity or has reached its usage limit."
        error_msg = ("Sorry, all of our bArIstas are busy brewing coffee right now."
                    "Please try again later.")
        # error_msg = f"Sorry, I encountered an error: {str(e)}"
        st.session_state.messages.append({
            "role": "assistant", 
            "content": error_msg,
            "error": True
        })

def main():
    """Main application function."""
    init_session_state()
    display_header()
    display_sidebar()
    
    # Main chat area
    st.markdown("## 💬 Chat")
    
    # Check if agent is available
    if not AGENT_AVAILABLE:
        st.error(f"Import Error: {IMPORT_ERROR}")
        return
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.chat_message("assistant").write("""
            Hello! I'm your ZUS Coffee assistant. I can help you with:
            
            🧮 Mathematical calculations \n
            📍 Finding ZUS Coffee outlets  \n
            🛍️ Product recommendations and searches \n
            
            What ya sipping today?
            """)
        # Display conversation history
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                display_message("user", msg["content"])
            else:
                display_message(
                    "assistant", 
                    msg["content"], 
                    tool_info=msg.get("tool_info")
                )
    
    # Chat input
    st.markdown("---")
    
    # Handle example query from sidebar
    if "user_input" in st.session_state:
        user_input = st.session_state.user_input
        del st.session_state.user_input
        process_user_input(user_input)
        st.rerun()
    
    # Regular chat input
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_button = st.columns([4, 1])
        
        with col_input:
            user_input = st.text_input(
                "Type your message:",
                placeholder="Ask me anything about calculations, outlets, or products...",
                label_visibility="collapsed"
            )
        
        with col_button:
            submit_button = st.form_submit_button("Send", use_container_width=True)
        
        if submit_button and user_input:
            process_user_input(user_input)
            st.rerun()

if __name__ == "__main__":
    main()
