# Mindhive Assessment - AI Chatbot Engineer

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
5. Copy `.env.example` to `.env` and set your API keys and configuration (e.g., GEMINI_API_KEY).
6. (Optional) Build or update the vector store and database:
   - `python scripts/load_products.py`  # Loads product data
   - `python scripts/load_outlets.py`   # Loads outlet data

## Running the System

- **Start the FastAPI server:**
  ```bash
  python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
  ```
- **Run the Streamlit chatbot UI:**
  ```bash
  streamlit run zus_chatbot.py
  ```
- **Run tests:**
  ```bash
  pytest tests/
  python test_complete_system.py  # End-to-end system test
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
4. Move the sqlite3.exe into base project director
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

- **Chatbot Agent (`chatbot/`):**
  - Implements a multi-turn conversational agent using the LangChain ReAct pattern and Google Gemini LLM.
  - Uses three main tools: Calculator, ZUS_Outlets (Text2SQL), and ZUS_Products (RAG vector search).
  - Maintains session-based memory for context-aware conversations.
  - Handles tool selection, error recovery, and conversation flow.

- **Streamlit UI (`zus_chatbot.py`):**
  - Provides a modern, interactive web interface for users.
  - Visualizes tool usage, conversation history, and handles errors gracefully.

- **Data & Scripts (`data/`, `scripts/`):**
  - Contains product/outlet data, vector store, and scripts for scraping/loading data.

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
- **Robustness:** Handles unhappy flows, errors, and includes security measures.

## Testing

Includes tests for:
- Multi-turn conversation flows
- Error and edge cases
- API and tool integrations
- Security vulnerabilities

## License

This project is for assessment and demonstration purposes only.
