"""
ZUS Products Vector Store Builder
Creates a FAISS vector store from scraped ZUS drinkware products for retrieval.
"""

import json
import os
import pickle
from typing import List, Dict, Any
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

class ProductVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store with a sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.products = []
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        
    def create_product_documents(self, products: List[Dict[str, Any]]) -> List[str]:
        """Create searchable documents from product data, including colours and promotion details."""
        documents = []
        
        for product in products:
            # Format colours for display
            colours = product.get('colours', [])
            colours_text = ', '.join(colours) if colours else 'No colours specified'
            
            doc = f"""
            Product Name: {product.get('name', 'Unknown')}
            Category: {product.get('category', 'Unknown')}
            Price: {product.get('price', 'N/A')}
            Colours: {colours_text}
            Promotion: {product.get('promotion', 'N/A')}
            In Stock: {'Yes' if product.get('in_stock', True) else 'No'}
            
            Full Product Info: {product.get('name', '')} - {product.get('category', '')} drinkware item priced at {product.get('price', 'N/A')}. Available colours: {colours_text}. Promotion: {product.get('promotion', 'N/A')}.
            """.strip()
            
            documents.append(doc)
        
        return documents
    
    def build_index(self, products: List[Dict[str, Any]]):
        """Build FAISS index from product data."""
        print(f"Building vector store for {len(products)} products...")
        
        # Store products for later retrieval
        self.products = products
        
        # Create documents
        documents = self.create_product_documents(products)
        
        # Generate embeddings
        embeddings = self.model.encode(documents)
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        embeddings_f32 = embeddings.astype('float32')
        self.index.add(embeddings_f32)
        
        print(f"Vector store built with {self.index.ntotal} products")
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for products similar to the query."""
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        query_emb_f32 = query_embedding.astype('float32')
        scores, indices = self.index.search(query_emb_f32, top_k)
        
        # Return results with scores
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx != -1:  # Valid result
                product = self.products[idx].copy()
                product['similarity_score'] = float(score)
                product['rank'] = i + 1
                results.append(product)
        
        return results
    
    def save(self, directory: str = "data/vector_store"):
        """Save the vector store to disk."""
        os.makedirs(directory, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, os.path.join(directory, "products.index"))
        
        # Save products and metadata
        with open(os.path.join(directory, "products.pkl"), "wb") as f:
            pickle.dump(self.products, f)
        
        # Save model info
        metadata = {
            "model_name": self.model.model_name if hasattr(self.model, 'model_name') else "all-MiniLM-L6-v2",
            "dimension": self.dimension,
            "num_products": len(self.products)
        }
        
        with open(os.path.join(directory, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Vector store saved to {directory}")
    
    def load(self, directory: str = "data/vector_store"):
        """Load the vector store from disk."""
        # Load FAISS index
        self.index = faiss.read_index(os.path.join(directory, "products.index"))
        
        # Load products
        with open(os.path.join(directory, "products.pkl"), "rb") as f:
            self.products = pickle.load(f)
        
        # Load metadata
        with open(os.path.join(directory, "metadata.json"), "r") as f:
            metadata = json.load(f)
            self.dimension = metadata["dimension"]
        
        print(f"Vector store loaded with {len(self.products)} products")

def load_products_from_json(filepath: str = "data/zus_products.json") -> List[Dict[str, Any]]:
    """Load products from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            products = json.load(f)
        print(f"Loaded {len(products)} products from {filepath}")
        return products
    except FileNotFoundError:
        print(f"Products file not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []

def build_vector_store():
    """Main function to build the vector store."""
    # Load products from JSON
    products = load_products_from_json()
    
    if not products:
        print("No products found. Run scrape_products.py first")
        return
    
    print(f"Building vector store for {len(products)} products")
    
    # Create and build vector store
    vector_store = ProductVectorStore()
    vector_store.build_index(products)

    # Save vector store
    vector_store.save()
    
    # Test the vector store
    print("\n--- Testing Vector Store ---")
    test_queries = [
        "tumbler with lid",
        "ceramic mug",
        "travel cup",
        "cold drink container",
        "blue tumbler"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.search(query, top_k=3)
        for result in results:
            print(f"  - {result['name']} (Score: {result['similarity_score']:.3f})")

if __name__ == "__main__":
    build_vector_store()
