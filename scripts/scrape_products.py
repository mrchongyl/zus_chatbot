"""
ZUS Coffee Product Scraper using Gemini 2.0 Flash
Scrapes drinkware products from https://shop.zuscoffee.com/
"""

import requests
import json
import csv
import time
import os
from typing import List, Dict, Any
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Setup Gemini API configuration
def setup_gemini_api():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in .env file.")
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def scrape_products() -> List[Dict[str, Any]]:

    print("Starting product scraping")

    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        print("Failed to setup Gemini API. Exiting...")
        return []
    
    products = []
    
    # URLs to scrape for products
    pages_to_scrape = [
        "https://shop.zuscoffee.com/collections/drinkware",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for page_num, url in enumerate(pages_to_scrape, 1):
        try:
            print(f"Fetching page {page_num}: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Extract text content for processing
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = extract_clean_text_content(soup)
            
            # Save raw scraped text for debugging
            os.makedirs("data", exist_ok=True)
            with open(f"data/products_raw.txt", 'w', encoding='utf-8') as f:
                f.write(page_text)
            print(f"Saved raw data/products_raw.txt")
                        
            if not page_text.strip():
                print(f"No content found on page {page_num}")
                continue
            
            # Use Gemini to extract product information
            page_products = extract_products_with_gemini(model, page_text, page_num)
            
            if page_products:
                products.extend(page_products)
                print(f"Extracted {len(page_products)} products from page {page_num}")
            else:
                print(f"No products extracted from page {page_num}")
            
            # Rate limiting to respect API limits
            time.sleep(2)
            
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            continue
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue
    
    print(f"Total products collected: {len(products)}")
    return products
    
def extract_clean_text_content(soup) -> str:
    """Extract clean text content from HTML for processing."""
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Clean up the text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Truncate if too long (Gemini has token limits)
    if len(text) > 30000:
        text = text[:30000] + "..."
    
    return text

def extract_products_with_gemini(model, page_text: str, page_num: int) -> List[Dict[str, Any]]:
    """Use Gemini to extract product information from page text."""
    
    prompt = f"""
You are an expert data extraction assistant. Extract ZUS Coffee drinkware product information from the following webpage content.

TASK: Extract all ZUS Coffee drinkware products with their names, categories (mug, tumbler, bundle), prices, descriptions, and promotions.

REQUIREMENTS:
1. Extract ONLY ZUS Coffee drinkware products (tumblers, mugs, bundles, etc.)
2. Include product names, categories (categorize as "mug", "tumbler", or "bundle"), prices, descriptions, and promotions
3. Extract accurate pricing in Malaysian Ringgit (RM)
4. Set category to either "mug", "tumbler", or "bundle" for each product based on the product type
5. If the product has any tags or labels like "On Sale", "Buy 1 Free 1", "Save 30%", etc., include them in a new field called "promotion" (as a string, or empty if none)

OUTPUT FORMAT: Return a valid JSON array with this exact structure:
[
  {{
    "name": "[Product Name]",
    "category": "[Product Category - mug/tumbler/bundle]",
    "price": "[Price in RM format - e.g., RM 25.90]",
    "description": "[Product description if available]",
    "promotion": "[Promotion label if any, or empty]",
    "in_stock": true
  }}
]

EXAMPLES:
- Name: "ZUS Tumbler Premium", category: "tumbler", price: "RM 29.90", promotion: "On Sale"
- Name: "ZUS Travel Mug", category: "mug", price: "RM 45.90", promotion: ""

IMPORTANT RULES:
- Only extract actual products with clear names and prices
- Categorize as "mug", "tumbler", or "bundle" based on the product type
- Include price in RM format
- Set in_stock to true unless clearly marked as out of stock
- Extract any visible promotion, offer, or tag (e.g., "On Sale", "Buy 1 Free 1", "Save 30%") into the "promotion" field

WEBPAGE CONTENT:
{page_text}

Extract the products as a JSON array:
"""

    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            return []
        
        # Clean the response to extract JSON
        json_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        
        json_text = json_text.strip()
        
        # Parse JSON
        products_data = json.loads(json_text)
        
        # Process and enhance the extracted data
        processed_products = []
        for i, product in enumerate(products_data):
            if not product.get('name') or not product.get('price'):
                continue
                
            # Generate additional fields
            product_id = f"product_{i+1:02d}"
            
            processed_product = {
                'id': product_id,
                'name': product.get('name', '').strip(),
                'category': product.get('category', '').strip().lower(),
                'price': product.get('price', 'N/A').strip(),
                'description': product.get('description', 'No description available').strip(),
                "promotion": product.get('promotion', 'N/A').strip(),
                'in_stock': product.get('in_stock', True),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            processed_products.append(processed_product)
            print(f"Extracted: {processed_product['name']} - {processed_product['price']}")
        
        return processed_products
        
    except json.JSONDecodeError as e:
        print(f"Error parsing response as JSON: {e}")
        return []
    except Exception as e:
        print(f"Error in extraction: {e}")
        return []


def save_products_to_csv(products: List[Dict[str, Any]], filename: str = "data/zus_products.csv"):
    
    if not products:
        print("No products to save")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = products[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
    
    print(f"Saved {len(products)} products to {filename}")

def save_products_to_json(products: List[Dict[str, Any]], filename: str = "data/zus_products.json"):
    """Save scraped products to JSON file."""
    
    if not products:
        print("No products to save")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(products, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(products)} products to {filename}")

if __name__ == "__main__":
    # Scrape products
    products = scrape_products()
    
    # Save to both CSV and JSON
    save_products_to_csv(products)
    save_products_to_json(products)
