"""
Simple script to randomly assign opening and closing hours to ZUS Coffee outlets.
"""

import csv
import json
import sqlite3
import random

def main():    
   
    # Define possible opening and closing hours
    opening_hours = ['06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '10:00']
    closing_hours = ['18:00', '19:00', '20:00', '21:00', '21:30', '22:00', '22:30', '23:00']
    
    # Load outlets from CSV
    outlets = []
    try:
        with open('data/zus_outlets.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                outlets.append(row)
        print(f"Loaded {len(outlets)} outlets")
    except FileNotFoundError:
        print("CSV file not found")
        return
    
    # Randomly assign hours
    for outlet in outlets:
        outlet['opening_time'] = random.choice(opening_hours)
        outlet['closing_time'] = random.choice(closing_hours)
        print(f"Updated {outlet['name'][:30]}... | {outlet['opening_time']}-{outlet['closing_time']}")
    
    # Save to CSV
    with open('data/zus_outlets.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = outlets[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(outlets)
    print("CSV updated")
    
    # Save to JSON
    with open('data/zus_outlets.json', 'w', encoding='utf-8') as f:
        json.dump(outlets, f, indent=2, ensure_ascii=False)
    print("JSON updated")
    
    # Update database
    try:
        conn = sqlite3.connect('data/outlets.db')
        cursor = conn.cursor()
        for outlet in outlets:
            cursor.execute("""
                UPDATE outlets 
                SET opening_time = ?, closing_time = ?
                WHERE id = ?
            """, (outlet['opening_time'], outlet['closing_time'], outlet['id']))
        conn.commit()
        # Show sample data
        cursor.execute('SELECT name, area, state, opening_time, closing_time, direction_url FROM outlets LIMIT 3')
        sample = cursor.fetchall()
        print("\nSample outlets:")
        for outlet in sample:
            print(outlet)
        conn.close()
        print("Database updated")
    except Exception as e:
        print(f"Database error: {e}")
    
    print("Done!")

if __name__ == "__main__":
    main()
