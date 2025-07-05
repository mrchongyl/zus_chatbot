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

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Mindhive Assessment API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)