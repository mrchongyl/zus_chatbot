# API endpoints for outlets Text2SQL queries.
# Text to SQL conversion for ZUS outlet data.


from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
import datetime

load_dotenv()

router = APIRouter(prefix="/outlets", tags=["outlets"])

# Database configuration
DATABASE_PATH = "data/outlets.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

class Text2SQLConverter:
    """Converts natural language queries to SQL for outlets database."""
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def convert_to_sql(self, natural_query: str) -> str:
        """Convert natural language query to SQL using Gemini 2.0 Flash."""
        
        if not self.model:
            raise HTTPException(status_code=503, detail="Gemini API not available")
        
        # Preprocess the query for time conversion
        processed_query = self.preprocess_query(natural_query)
        
        # Add current time info
        now = datetime.datetime.now()
        current_time_str = now.strftime("%H:%M:%S")
        
        system_prompt = f"""
        Convert natural language to SQL for ZUS coffee outlets.

        Current datetime: {current_time_str}

        Schema: outlets(id, name, address, area, state, opening_time, closing_time)

        Rules: 
        - ALWAYS select only the relevant columns: id, name, address, area, state, opening_time, closing_time (never use SELECT *), LIKE with %, case-insensitive, LIMIT 5, SQLite syntax
        - Auto-convert time: AM/PM to 24hr format (8 AM → 08:00, 10 PM → 22:00)
        
        IMPORTANT: 
        - Always detect and convert any Malaysian location initialisms (e.g., "PJ", "KL") into their full names (e.g., "Petaling Jaya", "Kuala Lumpur"). Ensure that all name/area/state abbreviations are expanded to their full forms prior to execution.

        Examples:
        - "Find outlets in Kuala Lumpur" → SELECT id, name, address, area, state, opening_time, closing_time FROM outlets WHERE area LIKE '%Kuala Lumpur%' OR state LIKE '%Kuala Lumpur%' OR name LIKE '%Kuala Lumpur%' LIMIT 5;
        - "Open until 10 PM" → SELECT id, name, address, area, state, opening_time, closing_time FROM outlets WHERE closing_time >= '22:00' LIMIT 5;
        - "What outlets are open now?" → SELECT id, name, address, area, state, opening_time, closing_time FROM outlets WHERE opening_time <= strftime('%H:%M', 'now', 'localtime') AND closing_time >= strftime('%H:%M', 'now', 'localtime') LIMIT 5;
        - "1 Utama opening hours" → SELECT id, name, address, area, state, opening_time, closing_time FROM outlets WHERE name LIKE '%1 Utama%' OR area LIKE '%1 Utama%' LIMIT 5;

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
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess the query to handle time conversions and context."""
    
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

def execute_sql_query(sql_query: str) -> List[Dict[str, Any]]:
    """Execute SQL query and return results."""
    
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

@router.get("/")
async def query_outlets(
    query: str = Query(..., description="Natural language query about outlets")
):
    """
    Convert natural language query to SQL and return outlet information.
    """

    try:
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
    """Test endpoint to verify database connectivity."""
    
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
