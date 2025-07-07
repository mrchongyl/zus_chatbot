"""
ZUS Coffee Outlet Scraper using Gemini
Scrapes outlet information from https://zuscoffee.com/category/store/kuala-lumpur-selangor/
"""

import requests
import json
import csv
import time
import os
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

BASE_URL = "https://zuscoffee.com/category/store/kuala-lumpur-selangor/"
MAX_PAGES = 11
MIN_OUTLETS_PER_PAGE = 5
MAX_EXTRACTION_RETRIES = 3
SAVE_RAW_FILES = True
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# --- Gemini API Setup ---
def setup_gemini_api():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not set.")
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-lite')

# --- Fetch HTML with Retries ---
def fetch_with_retries(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Fetch failed ({e}), retrying {attempt+1}/{max_retries}...")
            time.sleep(10)
    return None

# --- Extract Clean Text Content ---
def extract_clean_text_content(soup) -> Tuple[str, List[Dict[str, str]]]:
    outlet_blocks = []
    articles = soup.find_all("article")
    print(f"Found {len(articles)} <article> blocks")
    skip_names = {"Ingredients", "KCAL", ""}
    for idx, article in enumerate(articles):
        try:
            ps = article.find_all("p")
            name = ps[0].get_text(strip=True) if len(ps) > 0 else ""
            address = ps[1].get_text(strip=True) if len(ps) > 1 else ""
            # Filter: Unwanted extras like "Ingredients" and "KCAL"
            if name in skip_names or address in skip_names:
                continue
            # Search for the <a> link that contains 'maps.app.goo.gl'
            direction_url = ""
            for a in article.find_all("a", href=True):
                href = a['href'].strip()
                if "maps.app.goo.gl" in href:
                    direction_url = href
                    break
            # Only add if all three fields are present and direction_url is not empty
            if name and address and direction_url:
                outlet_blocks.append({
                    "name": name,
                    "address": address,
                    "direction_url": direction_url
                })
        except Exception as e:
            print(f"Error parsing article {idx}: {e}")
            continue
    # Combined text for debugging or Gemini input
    page_text = "\n".join([
        f"{outlet['name']}\n{outlet['address']}\nDirection: {outlet['direction_url']}"
        for outlet in outlet_blocks
    ])
    return page_text, outlet_blocks

# --- Gemini Outlet Extraction ---
def extract_outlets_with_gemini(model, outlet_blocks: list, page_num: int, start_index: int) -> List[Dict[str, Any]]:
    prompt = f"""
    Below is structured ZUS Coffee outlet data scraped from a webpage.

    Each outlet contains a name, full address, and a Google Maps direction URL.

    TASK: For each outlet:
    - Extract 'area' (town/city) and 'state' from the address
    - Return name, address, area, state, and direction_url

    OUTPUT FORMAT: Return a valid JSON array with this exact structure:
    [
    {{
        "name": "...",
        "address": "...",
        "area": "[Extracted area from address]",
        "state": "[Extracted state from address]",
        "direction_url": "..."
    }}
    ]

    OUTLETS:
    {json.dumps(outlet_blocks, indent=2)}

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
            outlet_id = f"outlet_{start_index + i:02d}"

            processed_outlet = {
                'id': outlet_id,
                'name': outlet.get('name', ''),
                'address': outlet.get('address', ''),
                'area': outlet.get('area', ''),
                'state': outlet.get('state', ''),
                'direction_url': outlet.get('direction_url', ''),
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

# --- Scrape Outlets Initialization ---
def scrape_outlets() -> List[Dict[str, Any]]:
    print("Starting outlet scraping")
    # Setup Gemini
    model = setup_gemini_api()
    if not model:
        print("Failed to setup Gemini API. Exiting...")
        return []
    outlets = []
    outlet_counter = 1
    pages_to_scrape = [BASE_URL] + [f"{BASE_URL}page/{i}/" for i in range(2, MAX_PAGES + 1)]
    headers = {'User-Agent': USER_AGENT}
    for page_num, url in enumerate(pages_to_scrape, 1):
        try:
            print(f"Fetching page {page_num}: {url}")
            outlet_blocks = []
            for extraction_attempt in range(MAX_EXTRACTION_RETRIES):
                response = fetch_with_retries(url, headers)
                if response is None:
                    print(f"Failed to fetch {url} after retries.")
                    break
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text, outlet_blocks = extract_clean_text_content(soup)
                # Save raw scraped text for debugging
                if SAVE_RAW_FILES:
                    os.makedirs("data", exist_ok=True)
                    with open(f"data/outlets_raw_page{page_num}.txt", 'w', encoding='utf-8') as f:
                        f.write(page_text)
                    print(f"Saved raw data/outlets_raw_page{page_num}.txt")
                if not page_text.strip():
                    print(f"No content found on page {page_num}")
                    break
                if len(outlet_blocks) >= MIN_OUTLETS_PER_PAGE:
                    break  # Success, enough outlets found
                print(f"Only {len(outlet_blocks)} outlets found on page {page_num}, retrying extraction ({extraction_attempt+1}/{MAX_EXTRACTION_RETRIES})...")
                time.sleep(10)  # Wait before retrying
            if not outlet_blocks or len(outlet_blocks) < MIN_OUTLETS_PER_PAGE:
                print(f"Insufficient outlets ({len(outlet_blocks)}) on page {page_num} after retries, skipping.")
                continue
            
            # Use Gemini to extract outlet information
            page_outlets = extract_outlets_with_gemini(model, outlet_blocks, page_num, outlet_counter)
            if page_outlets:
                outlets.extend(page_outlets)
                outlet_counter += len(page_outlets)
                print(f"Extracted {len(page_outlets)} outlets from page {page_num}")
            else:
                print(f"No outlets extracted from page {page_num}")
            
            # Rate limiting to respect API limits
            time.sleep(5)
        except requests.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            continue
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue
    print(f"Total outlets collected: {len(outlets)}")
    return outlets

# --- Save to CSV ---
def save_outlets_to_csv(outlets: List[Dict[str, Any]], filename: str = "data/zus_outlets.csv"):
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

# --- Save to JSON ---
def save_outlets_to_json(outlets: List[Dict[str, Any]], filename: str = "data/zus_outlets.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(outlets, jsonfile, indent=2, ensure_ascii=False)
    print(f"Saved {len(outlets)} outlets to {filename}")

if __name__ == "__main__":
    outlets = scrape_outlets()
    save_outlets_to_csv(outlets)
    save_outlets_to_json(outlets)
