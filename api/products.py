"""
Product RAG API
Provides /products endpoint for querying ZUS drinkware products using vector search
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Add the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.load_products import ProductVectorStore
except ImportError as e:
    print(f"Error importing ProductVectorStore: {e}")
    ProductVectorStore = None

# Load environment variables
load_dotenv()
router = APIRouter(prefix="/products", tags=["products"])

# Global vector store instance
vector_store = None

# Setup Gemini API configuration
def setup_gemini_api():
   
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')

# Load the vector store on startup
def load_vector_store():
   
    global vector_store
    
    if ProductVectorStore is None:
        print("ProductVectorStore class not available. Please check imports.")
        vector_store = None
        return
        
    try:
        vector_store = ProductVectorStore()
        vector_store.load("data/vector_store")
        print("Vector store loaded successfully")
    except Exception as e:
        print(f"Failed to load vector store: {e}")
        print("Please run load_products.py first")
        vector_store = None

# Generate an summary of the search results
def generate_ai_summary(query: str, products: List[Dict[str, Any]], model) -> str:
    
    if not products:
        return "No products found matching your query. Please try different search terms."
    
    # Create context from the search results
    products_context = []
    for i, product in enumerate(products, 1):

        # Convert colours from string to plain text
        colours = product.get('colours', [])
        colours_text = ', '.join(colours) if colours else 'No colour details'

        context = f"""
        {i}. {product['name']}
        - Price: {product['price']}
        - Promotion: {product['promotion']}
        - Category: {product['category']}
        - Colours: {colours_text}
        - In Stock: {'Yes' if product['in_stock'] else 'No'}
        - Similarity Score: {product.get('similarity_score', 0):.3f}
        """.strip()
        products_context.append(context)
    context_text = "\n\n".join(products_context)
    
    prompt = f"""
    You are a helpful customer service assistant for ZUS Coffee's drinkware products. 

    User Query: "{query}"

    Based on the following search results from our drinkware collection, provide a helpful and informative summary (1 paragraph maximum):

    {context_text}

    Please provide a response that:
    1. Directly addresses the user's query
    2. Highlights the most relevant products found
    3. Mentions key features like capacity, materials, special collections
    4. Includes pricing information, including promotion
    5. Suggests alternatives if appropriate
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        # Fallback to simple summary
        product_names = [p['name'] for p in products[:3]]
        return f"Found {len(products)} drinkware products matching '{query}'. Top matches include: {', '.join(product_names)}."

# Initialize vector store at module level
def init_vector_store():

    global vector_store
    if not vector_store:
        load_vector_store()

# Validate the natural language query for products
def validate_product_query(query: str) -> str | None:
   
    if not query or not query.strip():
        return "No products found matching your search criteria. Please enter a product keyword."
    if not re.search(r"[a-zA-Z0-9]", query):
        return "Please enter a valid product keyword."
    if len(query) > 100 or len(query.split()) > 20:
        return "Query too long. Please shorten your query."
    return None


@router.get("")
async def search_products(
    
    query: str = Query(..., description="Search query for products"),
    top_k: int = Query(5, ge=1, le=10, description="Number of top results to return"), # Default top-k to 5 if none specified
    include_summary: bool = Query(True, description="Include AI-generated summary")):
    """
    Search for ZUS drinkware products and return AI-generated summary
    query: Search query (e.g., "tumbler with lid", "ceramic mug")
    top_k: Number of top results to return (1-20)
    include_summary: Whether to include AI-generated summary
    Returns:
    JSON response with search results and AI summary
    """
    if not vector_store:
        init_vector_store()
        if not vector_store:
            raise HTTPException(
                status_code=503, 
                detail="Vector store not available."
            )
    
    error_msg = validate_product_query(query)
    if error_msg:
        return {
            "query": query,
            "products": [],
            "summary": error_msg,
            "total_results": 0
        }
    
    try:
        # Search for products
        results = vector_store.search(query, top_k=top_k)
        
        if not results:
            return {
                "query": query,
                "products": [],
                "summary": "No products found matching your search criteria. Please try different keywords.",
                "total_results": 0
            }
        
        response_data = {
            "query": query,
            "products": results,
            "total_results": len(results)
        }
        
        # Generate AI summary if requested
        if include_summary:
            try:
                model = setup_gemini_api()
                summary = generate_ai_summary(query, results, model)
                response_data["summary"] = summary
            except Exception as e:
                print(f"Error generating summary: {e}")
                response_data["summary"] = f"Found {len(results)} products matching your query."
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# Search for products and return raw results without AI summary (debugging)
@router.get("/raw")
async def search_products_raw(
    query: str = Query(..., description="Search query for products"),
    top_k: int = Query(5, ge=1, le=10, description="Number of top results to return")
):
    if not vector_store:
        init_vector_store()
        if not vector_store:
            raise HTTPException(
                status_code=503, 
                detail="Vector store not available."
            )
    
    try:
        results = vector_store.search(query, top_k=top_k)
        
        return {
            "query": query,
            "products": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

# Test endpoint to verify vector store connectivity
@router.get("/test")
async def health_check():
    if not vector_store:
        init_vector_store()
        
    return {
        "status": "healthy",
        "vector_store_loaded": vector_store is not None,
        "num_products": len(vector_store.products) if vector_store else 0,
        "message": "Vector store initialized successfully"
    }

# Initialize vector store