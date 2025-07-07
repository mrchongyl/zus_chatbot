"""
Calculator API
Evaluating mathematical expressions using asteval
"""

from fastapi import APIRouter
from pydantic import BaseModel
from asteval import Interpreter
import re

router = APIRouter(prefix="/calculator", tags=["calculator"])

# Response model
class CalcOutput(BaseModel):
    expression: str
    result: float | str
    success: bool
    error: str | None = None

# Initialize asteval
aeval = Interpreter()

# Validate the mathematical expression
def validate_expression(expr: str) -> str | None:
    
    if not expr or not expr.strip():
        return "No expression provided. Please enter a calculation."
    if len(expr) > 100 or len(expr.split()) > 20:
        return "Expression too long. Please shorten your calculation."
    if not re.match(r'^[0-9+\-*/().\s]+$', expr):
        return "Invalid characters in expression"
    return None

# API endpoint to evaluate mathematical expressions
@router.get("/")
async def calculate_get(expression: str):
   
    expr = expression

    # Streamlined input validation
    error_msg = validate_expression(expr)
    if error_msg:
        return CalcOutput(
            expression=expr,
            result="Error",
            success=False,
            error=error_msg
        )

    try:
        # Clear previous results
        aeval.symtable.clear()

        # Evaluate using asteval
        answer = aeval(expr)

        # Check for evaluation errors
        if aeval.error:
            err_msg = str(aeval.error[0].get_error())
            return CalcOutput(
                expression=expr,
                result="Error",
                success=False,
                error=err_msg
            )

        return CalcOutput(
            expression=expr,
            result=answer,
            success=True
        )

    except Exception as e:
        return CalcOutput(
            expression=expr,
            result="Error",
            success=False,
            error=str(e)
        )