#!/usr/bin/env python3
"""
Test script for calculator.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from api.calculator import calculate_post, CalcInput

async def test_calculator():
    """Test the calculator functionality."""
    print("Testing Calculator API")
    print("=" * 30)
    
    test_cases = [
        "2+2",
        "10*5+3", 
        "(15+5)/4",
        "2**3",
        "100/0",  # Division by zero test
        "2++2",   # Invalid syntax test
        "import os",  # Security test
    ]
    
    for i, expr in enumerate(test_cases, 1):
        print(f"\nTest {i}: {expr}")
        try:
            result = await calculate_post(CalcInput(expression=expr))
            print(f"  Success: {result.success}")
            print(f"  Result: {result.result}")
            if result.error:
                print(f"  Error: {result.error}")
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_calculator())
