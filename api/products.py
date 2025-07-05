# Product RAG API
# Provides /products endpoint for querying ZUS drinkware products using vector search

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.load_products import ProductVectorStore
except ImportError as e:
    print(f"Error importing ProductVectorStore: {e}")
    ProductVectorStore = None

# Load environment variables
load_dotenv()

# Create router instead of app
router = APIRouter(prefix="/products", tags=["products"])

# Global vector store instance
vector_store = None

def setup_gemini_api():
    """Setup Gemini API configuration."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def load_vector_store():
    """Load the vector store on startup."""
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

def generate_ai_summary(query: str, products: List[Dict[str, Any]], model) -> str:
    """Generate an summary of the search results."""
    
    if not products:
        return "No products found matching your query. Please try different search terms."
    
    # Create context from the search results
    products_context = []
    for i, product in enumerate(products, 1):
        context = f"""
        {i}. {product['name']}
           - Category: {product['category']}
           - Price: {product['price']}
           - Description: {product['description']}
           - In Stock: {'Yes' if product['in_stock'] else 'No'}
           - Similarity Score: {product.get('similarity_score', 0):.3f}
        """.strip()
        products_context.append(context)
    
    context_text = "\n\n".join(products_context)
    
    prompt = f"""
You are a helpful customer service assistant for ZUS Coffee's drinkware products. 

User Query: "{query}"

Based on the following search results from our drinkware collection, provide a helpful and informative summary:

{context_text}

Please provide a response that:
1. Directly addresses the user's query
2. Highlights the most relevant products found
3. Mentions key features like capacity, materials, special collections
4. Includes pricing information, including promotion
5. Suggests alternatives if appropriate

Keep the response concise but informative (2 paragraphs maximum).
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
    """Initialize vector store when module is imported."""
    global vector_store
    if not vector_store:
        load_vector_store()

@router.get("")
async def search_products(
    query: str = Query(..., description="Search query for products"),
    top_k: int = Query(5, ge=1, le=20, description="Number of top results to return"),
    include_summary: bool = Query(True, description="Include AI-generated summary")
):
    """
    Search for ZUS drinkware products and return AI-generated summary.
    
    Args:
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
    
    try:
        # Search for products
        results = vector_store.search(query, top_k=top_k)
        
        if not results:
            return {
                "query": query,
                "summary": "No products found matching your search criteria. Please try different keywords.",
                "products": [],
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

@router.get("/raw")
async def search_products_raw(
    query: str = Query(..., description="Search query for products"),
    top_k: int = Query(5, ge=1, le=20, description="Number of top results to return")
):
    """
    Search for products and return raw results without AI summary.
    Useful for debugging or when you don't need AI processing.
    """
    
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

@router.get("/test")
async def health_check():
    """Test endpoint to verify vector store connectivity."""
    if not vector_store:
        init_vector_store()
        
    return {
        "status": "healthy",
        "vector_store_loaded": vector_store is not None,
        "num_products": len(vector_store.products) if vector_store else 0,
        "message": "Vector store initialized successfully"
    }

# Initialize vector store when module is imported
init_vector_store()