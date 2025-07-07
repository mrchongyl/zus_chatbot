"""
Load Outlets to Database
=======================

This script loads the scraped ZUS outlet data from CSV into SQLite database.
Run this after scraping outlets data.

Usage:
    python scripts/load_outlets.py
"""

import sqlite3
import csv
import os
from pathlib import Path

def create_database():
    """Create the outlets database and table."""
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect('data/outlets.db')
    cursor = conn.cursor()
    
    # Drop the table if it exists to avoid schema mismatch
    cursor.execute('DROP TABLE IF EXISTS outlets')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outlets (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            address TEXT NOT NULL,
            area VARCHAR NOT NULL,
            state VARCHAR NOT NULL,
            opening_time TIME,
            closing_time TIME,
            direction_url TEXT,
            scraped_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def load_outlets_from_csv():
    """Load outlet data from CSV file into database."""
    
    csv_file = Path('data/zus_outlets.csv')
    
    if not csv_file.exists():
        print("CSV file not found: data/zus_outlets.csv")
        print("Run: python scripts/scrape_outlets.py first")
        return False
    
    # Create database
    conn = create_database()
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM outlets')
    print("Cleared existing outlet data")
    
    # Load data from CSV
    outlets_loaded = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                cursor.execute('''
                    INSERT OR REPLACE INTO outlets 
                    (id, name, address, area, state, opening_time, closing_time, direction_url, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('id', ''),
                    row.get('name', ''),
                    row.get('address', ''),
                    row.get('area', ''),
                    row.get('state', ''),
                    row.get('opening_time', ''),
                    row.get('closing_time', ''),
                    row.get('direction_url', ''),
                    row.get('scraped_at', '')
                ))
                outlets_loaded += 1
        
        conn.commit()
        print(f"Loaded {outlets_loaded} outlets into database")
        
        # Show sample data
        #print("\n--- Testing Database ---")
        cursor.execute('SELECT name, area, state, opening_time, closing_time, direction_url FROM outlets LIMIT 3')
        sample = cursor.fetchall()
        print("\nSample outlets:")
        for outlet in sample:
            print(outlet)
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Main function to load outlets."""
    print("Loading Outlets to Database")    
    success = load_outlets_from_csv()
    print("\nDatabase loading completed!")

if __name__ == "__main__":
    main()
