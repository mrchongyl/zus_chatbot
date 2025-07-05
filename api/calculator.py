# API endpoints for calculator.

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

@router.get("/")
async def calculate_get(expression: str):
    expr = expression

    # Only allow numbers and arithmetic characters
    if not re.match(r'^[0-9+\-*/().\s]+$', expr):
        return CalcOutput(
            expression=expr,
            result="Error",
            success=False,
            error="Invalid characters in expression"
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
    
@router.get("/test")
async def health_check():
    """Health check endpoint for calculator API."""
    try:
        # Simple calculation to test asteval
        aeval.symtable.clear()
        test_expr = "1+1"
        answer = aeval(test_expr)
        error = None
        if aeval.error:
            error = str(aeval.error[0].get_error())
        return {
            "status": "healthy",
            "test_expression": test_expr,
            "test_result": answer,
            "asteval_error": error,
            "message": "Calculator is operational"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Calculator health check failed: {str(e)}"
        }