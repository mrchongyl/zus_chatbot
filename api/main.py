"""
FastAPI server for the Mindhive Assessment chatbot.
This module contains the main API endpoints for:
- Product knowledge base retrieval
- Outlets Text2SQL queries
- Calculator tool integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import calculator, products, outlets
from fastapi import status
import os
import google.generativeai as genai

app = FastAPI(
    title="Mindhive Assessment API",
    description="Zus Coffee Chatbot API with RAG and Tool Integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(calculator.router)
app.include_router(products.router)
app.include_router(outlets.router)

# Root endpoint for health check
@app.get("/")
async def root():
    return {"message": "Mindhive Assessment API is running"}

@app.get("/health", summary="Health check for all subsystems")
async def health_check():
    health = {}

    # Check Calculator API (basic check)
    try:
        from .calculator import validate_expression
        calc_result = validate_expression("1+1")
        health["calculator"] = "ok" if calc_result is None else f"fail: {calc_result}"
    except Exception as e:
        health["calculator"] = f"fail: {e}"

    # Check Products API (vector store)
    try:
        from .products import vector_store
        health["products_vector_store"] = "ok" if vector_store else "missing"
    except Exception as e:
        health["products_vector_store"] = f"fail: {e}"

    # Check Outlets API (database)
    try:
        from .outlets import DATABASE_PATH
        health["outlets_db"] = "ok" if os.path.exists(DATABASE_PATH) else "missing"
    except Exception as e:
        health["outlets_db"] = f"fail: {e}"

    overall = all(v == "ok" for v in health.values())
    return {
        "status": "ok" if overall else "degraded",
        "details": health
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=True) 
    
    # uvicorn.run(app, host="127.0.0.1", port=8000, reload=True) for local development