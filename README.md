# Mindhive Assessment - ZUS Chatbot

This project implements a multi-turn conversational AI chatbot with agentic planning, tool integration, and Retrieval-Augmented Generation (RAG) for the Mindhive Assessment.

## Project Structure

```
├── api/              # FastAPI server code and endpoints
├── chatbot/          # Core chatbot agent logic and planning
├── data/             # Database and scraped data (products, outlets)
├── scripts/          # Data scraping and ingestion scripts
├── tests/            # Automated and integration tests
├── .venv/            # Python virtual environment
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

## Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `./.venv/Scripts/activate`
   - Mac/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` to set your API keys and configuration (e.g., GEMINI_API_KEY).
6. (Optional) Build or update the vector store and database:
   - `python scripts/load_products.py`  # Loads product data
   - `python scripts/load_outlets.py`   # Loads outlet data

## Running the System

- **Start the FastAPI server:**
  ```bash
  python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
  ```
  - The vector store is now loaded once at server startup (see `@app.on_event("startup")` in `api/main.py`).
  - If the vector store is missing or corrupted, endpoints will return a 503 error until it is rebuilt.
- **Run the Streamlit chatbot UI:**
  ```bash
  python -m streamlit run zus_chatbot.py
  ```
- **Run tests:**
  ```bash
  pytest tests/
  ```
- **Run data scraping scripts:**
  ```bash
  python scripts/scrape_products.py
  python scripts/scrape_outlets.py
  ```

## Setting Up the SQLite Database

The system uses a SQLite database for ZUS Coffee outlet information. To set up the database:

1. Ensure you have Python 3.8+ installed.
2. Install the SQLite CLI for manual inspection: https://www.sqlite.org/download.html
3. Load the outlet data into the database by running:
   ```bash
   python scripts/load_outlets.py
   ```
   This will create `data/outlets.db` with all outlet information.
4. Move the sqlite3.exe into base project directory if you want to use the CLI.
5. To inspect the database manually:
   ```bash
   sqlite3 data/outlets.db
   # Then you can run SQL commands, e.g.:
   # .tables
   # SELECT * FROM outlets LIMIT 5;
   ```
6. If you need to rebuild or update the database, simply rerun the script above.

The API will not work until `data/outlets.db` exists and is populated.


## Architecture Overview

The system is composed of several modular components:

- **FastAPI Backend (`api/`):**
  - Exposes endpoints for calculator, product search (RAG), and outlet queries (Text2SQL).
  - Handles requests from both the chatbot agent and external clients.
  - Integrates with a vector store (FAISS) for semantic product search and a SQLite database for outlet info.
  - Implements a safe calculator API using asteval to evaluate user-submitted math expressions securely.
  - **Vector store is loaded at startup for performance.**

- **Chatbot Agent (`chatbot/`):**
  - Implements a multi-turn conversational agent using the LangChain ReAct pattern and Google Gemini LLM.
  - Uses three main tools: Calculator, ZUS_Outlets (Text2SQL), and ZUS_Products (RAG vector search).
  - Maintains session-based memory for context-aware conversations.
  - **Memory is limited to the last N turns for performance.**
  - Handles tool selection, error recovery, and conversation flow.

- **Streamlit UI (`zus_chatbot.py`):**
  - Provides a modern, interactive web interface for users.
  - Visualizes tool usage, conversation history, and handles errors gracefully.

- **Data & Scripts (`data/`, `scripts/`):**
  - Contains product/outlet data, vector store, and scripts for scraping/loading data.

## System Flowchart

Below is a flowchart illustrating the main components and data flow of the system, from user input to backend processing and data retrieval.

```
           User (via Streamlit UI)
                     │
                     ▼
        +-----------------------------+
        |     Streamlit Frontend      |
        |        (zus_chatbot.py)     |
        +-----------------------------+
                     │
                     ▼
        +-----------------------------+
        |        Chatbot Agent        |
        |           (chatbot/)        |
        | - Multi-turn conversation   |
        | - Agentic planning          |
        | - Tool selection            |
        +-----------------------------+
                     │
                     ▼
        +-----------------------------+
        |        FastAPI Backend      |
        |             (api/)          |
        | - Exposes API endpoints:    |
        |     • Calculator             |
        |     • ZUS_Products (RAG)     |
        |     • ZUS_Outlets (Text2SQL)|
        +-----------------------------+
           │           │           │
           ▼           ▼           ▼
+----------------+  +----------------+  +------------------+
|  Calculator     |  | Product Search |  |  Outlet Search   |
|    Tool (API)   |  |     (RAG)      |  |   (Text2SQL)     |
+----------------+  +----------------+  +------------------+
                            │                     │
                            ▼                     ▼
             +------------------+     +--------------------+
             | FAISS Vector DB  |     |   SQLite DB        |
             |   (data/)        |     | (data/outlets.db)  |
             +------------------+     +--------------------+
```

## Assessment Requirements Implementation

### Part 1: Sequential Conversation
- **Memory Management:** Session-based memory stores last several turns per user, enabling context-aware responses.
- **Context Awareness:** Previous conversation context is used to influence agent decisions and responses.
- **State Management:** Each user/session is isolated, ensuring global state does not leak between users.
- **Multi-turn Support:** The agent supports seamless multi-turn conversations, maintaining context and variables across turns.

### Part 2: Agentic Planning
- **Intent Classification:** User intent is parsed using the LangChain ReAct pattern and Google Gemini LLM.
- **Action Planning:** The agent selects and sequences tool/API calls based on parsed intent and conversation context.
- **Confidence Handling:** The agent leverages LLM output and error handling to determine when to ask clarifying questions or retry.
- **Core Intents:** Supported intents include calculation, product search (RAG), outlet search (Text2SQL), and general chat.

### Part 3: Tool Calling
- **Calculator Tool:** Mathematical expressions are evaluated safely using the asteval library, with input validation and error handling.
- **Natural Language Processing:** LLM-powered parsing of user queries to extract expressions and intent.
- **Security:** All tool calls are sandboxed and validated to prevent code injection or unsafe execution.
- **Error Handling:** The system provides clear, informative error messages and fallback responses for invalid input or tool failures.

### Part 4: Custom API & RAG Integration
- **Vector Search:** Product search is powered by FAISS-based semantic vector search for relevant product retrieval.
- **Text2SQL:** Natural language queries for outlets are converted to SQL using LLMs and executed against a SQLite database.
- **Embeddings:** Sentence-transformers are used to generate semantic embeddings for product data.
- **Database Integration:** SQLite is used for structured outlet data, with robust query validation.

### Part 5: Unhappy Flows
- **Input Validation:** All user input is sanitized and validated before processing.
- **Error Recovery:** The agent and APIs handle errors gracefully, providing fallback responses and suggestions.
- **Security:** SQL injection and code injection are prevented through input validation and safe execution practices.
- **Monitoring:** Health check endpoints and system status checks are implemented for operational monitoring.

### Key Trade-offs & Design Decisions

- **Agentic Planning (LangChain ReAct):**
  - Chosen for its ability to reason step-by-step, invoke tools, and maintain context across turns.
  - Trade-off: Slightly more complex to implement and debug, but enables robust multi-turn flows.

- **Tool Integration:**
  - Each tool (calculator, outlets, products) is a separate API endpoint, making the system modular and testable.
  - Trade-off: Requires careful error handling and API orchestration.

- **Retrieval-Augmented Generation (RAG):**
  - Uses FAISS vector search for semantic product queries, improving answer relevance.
  - Trade-off: Requires maintaining a vector store and periodic data updates.

- **Text2SQL for Outlets:**
  - Natural language queries are converted to SQL for flexible outlet search.
  - Trade-off: Relies on LLM accuracy for SQL generation; mitigated by error handling and query validation.

- **Session-based Memory:**
  - Enables context retention for multi-turn conversations.
  - Trade-off: Requires session management and memory cleanup.

- **Security & Robustness:**
  - Input validation, error handling, and environment variable management are implemented throughout.

## Features

- **Multi-turn Conversation:** Maintains state and tracks variables across user turns.
- **Agentic Planning:** Parses user intent and selects actions using planner/controller logic.
- **Tool Integration:** Integrates with a calculator API and handles errors gracefully.
- **Custom API & RAG:** 
  - FastAPI endpoints for ZUS coffee shop data (products, outlets).
  - Product knowledge base with vector search for RAG.
  - Outlets database with Text2SQL capabilities.
  - Calculator API powered by asteval for safely evaluating user math expressions.
- **Robustness:** Handles unhappy flows, errors, and includes security measures.

## Testing

Includes tests for:
- Multi-turn conversation flows
- Error and edge cases
- API and tool integrations
- Security vulnerabilities

### Test Suite Overview

The `tests/` directory contains comprehensive automated and integration tests for all major chatbot and API features:

- **test_calculator_tool.py**: Calculator tool tests (basic, failure, hacking, extreme input, centralized failure phrases, rate limiting)
- **test_agentic_planning.py**: Agentic planning tests (outlet/product/calculator/edge case variations, rate limiting)
- **test_agentic_planning_comprehensive.py**: Comprehensive agentic planning test
- **test_unhappy_flows_comprehensive.py**: Unhappy flows (wrong/missing params, unsupported methods, large/special queries, product tool edge cases)
- **test_sequential_conversation.py**: Sequential conversation, assertion logic
- **test_api_integration.py**: API integration tests for products and outlets
- **test_complete_system.py**: End-to-end system test

All tests are designed to cover both happy and unhappy flows, edge cases, and robust input validation. Centralized failure phrase lists and helper functions are used for maintainability and assertion consistency.

## License

This project is for assessment and demonstration purposes only.

## Local Deployment

To run the ZUS Chatbot system locally on your machine, follow these steps:

### 1. **Clone the Repository**

```bash
git clone https://github.com/your-username/zus_chatbot.git
cd zus_chatbot
```

### 2. **Set Up Python Environment**

- Create a virtual environment:
  ```bash
  python -m venv .venv
  ```
- Activate the environment:
  - On Windows:
    ```bash
    .\.venv\Scripts\activate
    ```
  - On Mac/Linux:
    ```bash
    source .venv/bin/activate
    ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 3. **Configure Environment Variables**

- Create a `.env` file in the project root.
- Add your API keys and configuration, for example:
  ```
  GEMINI_API_KEY=your_gemini_api_key_here
  ```

### 4. **Prepare Data**

- Load product and outlet data (required for chatbot functionality):
  ```bash
  python scripts/load_products.py
  python scripts/load_outlets.py
  ```

### 5. **Start the FastAPI Backend**

- Run the backend server:
  ```bash
  python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
  ```
- The vector store and database will be loaded at startup. If missing, endpoints will return a 503 error until data is loaded.

### 6. **Launch the Chatbot UI**

- In a new terminal (with the virtual environment activated), run:
  ```bash
  python -m streamlit run zus_chatbot.py
  ```
- This will open the chatbot interface in your browser at `http://localhost:8501`.

### 7. **Accessing the API**

- The FastAPI docs are available at:  
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check endpoint:  
  [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 8. **Troubleshooting**

- If you encounter errors about missing vector store or database, rerun the data loading scripts.
- For SQL/database errors, ensure `data/outlets.db` exists and is populated.
- For API key errors, check your `.env` file.


**You can now interact with the ZUS Chatbot locally, both via the web UI and the API.**

## Cloud Deployment

The ZUS Coffee chatbot is deployed on Google Cloud for reliable and scalable performance.
