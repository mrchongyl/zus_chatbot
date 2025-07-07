"""
ZUS Coffee Outlet Scraper using Gemini 2.0 Flash
Scrapes outlet information from https://zuscoffee.com/category/store/kuala-lumpur-selangor/
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
        print("Warning: GEMINI_API_KEY environment variable not set.")
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def scrape_outlets() -> List[Dict[str, Any]]:
    
    print("Starting outlet scraping")
    
    # Setup Gemini API
    model = setup_gemini_api()

    outlets = []
    
    # URLs to scrape
    base_url = "https://zuscoffee.com/category/store/kuala-lumpur-selangor/"
    max_pages = 2
    
    pages_to_scrape = [base_url]  # First page
    pages_to_scrape.extend([f"{base_url}page/{i}/" for i in range(2, max_pages + 1)])
    
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
            SAVE_RAW_FILES = False
            if SAVE_RAW_FILES:
                os.makedirs("data", exist_ok=True)
                with open(f"data/outlets_raw{page_num}.txt", 'w', encoding='utf-8') as f:
                    f.write(page_text)
                print(f"Saved raw data/outlets_raw{page_num}.txt")

            if not page_text.strip():
                print(f"No content found on page {page_num}")
                continue
            
            # Use Gemini to extract outlet information
            page_outlets = extract_outlets_with_gemini(model, page_text, page_num)
            
            if page_outlets:
                outlets.extend(page_outlets)
                print(f"Extracted {len(page_outlets)} outlets from page {page_num}")
            else:
                print(f"No outlets extracted from page {page_num}")
            
            # Rate limiting to respect API limits
            time.sleep(2)
            
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            continue
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue
    
    print(f"Total outlets collected: {len(outlets)}")
    return outlets

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

def extract_outlets_with_gemini(model, page_text: str, page_num: int) -> List[Dict[str, Any]]:
    """Use Gemini to extract outlet information from page text."""
    
    prompt = f"""
You are an expert data extraction assistant. Extract ZUS Coffee outlet information from the following webpage content.

TASK: Extract all ZUS Coffee outlets with their complete and accurate information.

REQUIREMENTS:
1. Each outlet must have a unique and correct name-address pairing
2. Ensure outlet names match their corresponding addresses
3. Extract the 'area' (city/town) and 'state' from the address field, and include them as separate fields in the output. 
For example, if the address ends with 'Shah Alam, Selangor', then area is 'Shah Alam' and state is 'Selangor'.

OUTPUT FORMAT: Return a valid JSON array with this exact structure:
[
  {{
    "name": "ZUS Coffee – [Location Name]",
    "address": "[Complete physical address]",
    "area": "[Extracted area from address]",
    "state": "[Extracted state from address]"
    }}
]

IMPORTANT RULES:
- Ensure each outlet name correctly corresponds to its address
- Area and state must be extracted from the address and included as separate fields

WEBPAGE CONTENT:
{page_text}

Extract the outlets as a JSON array:
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
        outlets_data = json.loads(json_text)
        
        # Process and enhance the extracted data
        processed_outlets = []
        for i, outlet in enumerate(outlets_data):
            if not outlet.get('name') or not outlet.get('address'):
                continue
                
            # Generate additional fields
            outlet_id = f"outlet_{i+1:02d}"
            
            processed_outlet = {
                'id': outlet_id,
                'name': outlet.get('name', ''),
                'address': outlet.get('address', ''),
                'area': outlet.get('area', ''),
                'state': outlet.get('state', ''),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            processed_outlets.append(processed_outlet)
            print(f"Extracted: {processed_outlet['name']}")
        
        return processed_outlets
        
    except json.JSONDecodeError as e:
        print(f"Error parsing response as JSON: {e}")
        return []
    except Exception as e:
        print(f"Error in extraction: {e}")
        return []

def save_outlets_to_csv(outlets: List[Dict[str, Any]], filename: str = "data/zus_outlets1.csv"):

    if not outlets:
        print("No outlets to save to CSV.")
        return
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fieldnames = list(outlets[0].keys())
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for outlet in outlets:
            writer.writerow(outlet)
    print(f"Saved {len(outlets)} outlets to {filename}")

def save_outlets_to_json(outlets: List[Dict[str, Any]], filename: str = "data/zus_outlets1.json"):
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(outlets, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(outlets)} outlets to {filename}")

if __name__ == "__main__":
    # Scrape outlets with Gemini
    outlets = scrape_outlets()
    
    # Save to both CSV and JSON
    save_outlets_to_csv(outlets)
    save_outlets_to_json(outlets)
