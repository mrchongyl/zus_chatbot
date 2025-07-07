"""
ZUS Coffee Product Scraper using Gemini 2.0 Flash-Lite
Scrapes drinkware products from https://shop.zuscoffee.com/collections/drinkware
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

PRODUCT_URLS = [
    "https://shop.zuscoffee.com/collections/drinkware",
]
SAVE_RAW_FILES = True
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Setup Gemini API configuration
def setup_gemini_api():
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in .env file.")
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

# Extract clean text content from HTML
def extract_clean_text_content(soup) -> str:
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text()
    
    # Clean up the text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Truncate if too long
    if len(text) > 30000:
        text = text[:30000] + "..."
    
    return text

# Extract product information using Gemini
def extract_products_with_gemini(model, page_text: str, page_num: int) -> List[Dict[str, Any]]:
    
    prompt = f"""
    You are an expert extractor. From the webpage below, extract **only ZUS Coffee drinkware** products (e.g., mugs, tumblers, bundles).

    For each product, include:
    - "name": Product name
    - "category": "mug", "tumbler", or "bundle"
    - "price": In RM format (e.g., "RM 25.90")
    - "colours": All available colours as a list of strings (e.g., ["Thunder Blue"])
    - "promotion": Any tags like "On Sale", "Buy 1 Free 1", etc., or empty string
    - "in_stock": true unless explicitly out of stock

    **Output:** Return a JSON array like:
    [
    {{
        "name": "...",
        "category": "...",
        "price": "...",
        "colours": [...],
        "promotion": "...",
        "in_stock": true
    }}
    ]

    **Rules:**
    - Only include drinkware products with clear names and prices
    - Categorize properly
    - Extract all colour options; use `[]` if none
    - Use RM format for price
    - Set `promotion` to matching label or empty
    - Default `in_stock` to true unless clearly out of stock

    **Webpage:**
    {page_text}

    Return only the JSON array:
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
                'colours': product.get('colours', []),
                'promotion': product.get('promotion', '').strip(),
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

def scrape_products() -> List[Dict[str, Any]]:

    print("Starting product scraping")

    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        print("Failed to setup Gemini API. Exiting...")
        return []
    
    products = []
    headers = {'User-Agent': USER_AGENT}
    
    for page_num, url in enumerate(PRODUCT_URLS, 1):
        try:
            print(f"Fetching page {page_num}: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Extract text content for processing
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = extract_clean_text_content(soup)
            
            # Save raw scraped text for debugging
            if SAVE_RAW_FILES:
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

# Save the scraped products to CSV and JSON files
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
    
    if not products:
        print("No products to save")
        return
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(products, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(products)} products to {filename}")

if __name__ == "__main__":
    products = scrape_products()
    save_products_to_csv(products)
    save_products_to_json(products)
