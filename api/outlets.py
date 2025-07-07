"""
Text2SQL API
Text to SQL conversion for ZUS outlet data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/outlets", tags=["outlets"])

# --- Database Configuration ---
DATABASE_PATH = "data/outlets.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# --- Text2SQL Converter ---
class Text2SQLConverter:
    # Setup Gemini API configuration
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
    # Convert natural language query to SQL using Gemini
    def convert_to_sql(self, natural_query: str) -> str:
        if not self.model:
            raise HTTPException(status_code=503, detail="Gemini API not available")
        # Preprocess the query for time conversion
        processed_query = self.preprocess_query(natural_query)
        system_prompt = f"""
        Convert user queries into SQLite SQL for ZUS Coffee outlets.

        Schema:
        outlets(id, name, address, area, state, opening_time, closing_time, direction_url)

        Rules:
        - Select only: id, name, address, area, state, opening_time, closing_time, direction_url (no SELECT *)
        - Use case-insensitive LIKE with %
        - Use LIMIT 5
        - Convert AM/PM to 24-hour format (e.g., 10 PM → 22:00)
        - Expand Malaysian abbreviations (e.g., "PJ" → "Petaling Jaya", "KL" → "Kuala Lumpur")
        - Use SQLite syntax (e.g., strftime for current time)

        Examples:
        - "Find outlets in Kuala Lumpur" → SELECT id, name, address, area, state, opening_time, closing_time, direction_url FROM outlets WHERE area LIKE '%Kuala Lumpur%' OR state LIKE '%Kuala Lumpur%' OR name LIKE '%Kuala Lumpur%' LIMIT 5;    
        - "Open until 10 PM" → SELECT id, name, address, area, state, opening_time, closing_time, direction_url  FROM outlets WHERE closing_time >= '22:00' LIMIT 5;
        - "What outlets are open now?" → SELECT id, name, address, area, state, opening_time, closing_time, direction_url  FROM outlets WHERE opening_time <= strftime('%H:%M', 'now', 'localtime') AND closing_time >= strftime('%H:%M', 'now', 'localtime') LIMIT 5;
        - "1 Utama opening hours" → SELECT id, name, address, area, state, opening_time, closing_time, direction_url FROM outlets WHERE name LIKE '%1 Utama%' OR area LIKE '%1 Utama%' LIMIT 5;

        Query: {processed_query}
        SQL:
        """
        try:
            response = self.model.generate_content(system_prompt)
            if not response.text:
                raise HTTPException(status_code=500, detail="Failed to generate SQL query")
            sql_query = response.text.strip()
            # Clean up the SQL query
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            if not sql_query.endswith(';'):
                sql_query += ';'
            return sql_query
        except Exception as e:
            print(f"Gemini API error: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating SQL query: {str(e)}")
    # Preprocess the query to handle time conversions and context.
    def preprocess_query(self, query: str) -> str:
        # Convert AM/PM times to 24-hour format
        def convert_time(match):
            time_str = match.group(0)
            # Extract hour, minute, and AM/PM
            time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM)'
            time_match = re.search(time_pattern, time_str, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                period = time_match.group(3).upper()
                # Convert to 24-hour format
                if period == 'AM':
                    if hour == 12:
                        hour = 0
                elif period == 'PM':
                    if hour != 12:
                        hour += 12
                return f"{hour:02d}:{minute:02d}"
            return time_str
        # Find and replace time patterns
        time_pattern = r'\b\d{1,2}(?::\d{2})?\s*[AP]M\b'
        processed_query = re.sub(time_pattern, convert_time, query, flags=re.IGNORECASE)
        return processed_query

# --- SQL Execution ---
def execute_sql_query(sql_query: str) -> List[Dict[str, Any]]:    
    if not os.path.exists(DATABASE_PATH):
        raise HTTPException(status_code=500, detail="Database not found. Please load database first.")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            # Convert result to list of dictionaries
            columns = list(result.keys())
            rows = []
            for row in result:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                rows.append(row_dict)
            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

# --- Query Validation ---
def validate_outlet_query(query: str) -> str | None:
    if not query or not query.strip():
        return "Please specify a location, area, or outlet name to search for."
    if not re.search(r"[a-zA-Z0-9]", query):
        return "Please enter a valid location, area, or outlet name."
    if len(query) > 100 or len(query.split()) > 20:
        return "Query too long. Please shorten your query."
    lowered = query.lower()
    if any(keyword in lowered for keyword in [";", "--", "drop ", "delete ", "insert ", "update ", "alter ", "truncate "]):
        return "Invalid or potentially unsafe query. Please rephrase your request."
    return None

# --- API Endpoints ---
@router.get("/")
async def query_outlets(
    query: str = Query(..., description="Natural language query about outlets")):
    try:
        error_msg = validate_outlet_query(query)
        if error_msg:
            return {
                "query": query,
                "sql": None,
                "results": [],
                "count": 0,
                "message": error_msg
            }
        # Convert natural language to SQL
        converter = Text2SQLConverter()
        sql_query = converter.convert_to_sql(query)
        # Execute SQL query
        results = execute_sql_query(sql_query)
        return {
            "query": query,
            "sql": sql_query,
            "results": results,
            "count": len(results),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/test")
async def health_check():    
    try:
        if not os.path.exists(DATABASE_PATH):
            return {
                "status": "error",
                "message": "Database not found. Please run: python scripts/load_database.py"
            }
        # Test query
        results = execute_sql_query("SELECT COUNT(*) as count FROM outlets;")
        outlet_count = results[0]['count'] if results else 0
        return {
            "status": "healthy",
            "database_path": DATABASE_PATH,
            "outlet_count": outlet_count,
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database test failed: {str(e)}"
        }
