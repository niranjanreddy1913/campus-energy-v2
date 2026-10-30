"""calculator.py — the logic, and nothing else: no FastAPI, no MCP, no web.
1_calculator_api.py (REST) calls it today; in Part 3 the MCP server calls the SAME function. Write the logic once, give it many doors."""

OPERATIONS = ("add", "sub", "mul", "div")


def calculate(a: float, b: float, op: str) -> float:
    """Apply one operation to two numbers. Refuses what maths can't do with a ValueError."""
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "mul":
        return a * b
    if op == "div":
        if b == 0:
            raise ValueError("cannot divide by zero")
        return a / b
    raise ValueError(f"unknown operation '{op}' — use one of {', '.join(OPERATIONS)}")


if __name__ == "__main__":                       # python calculator.py — the function works before any API exists
    print("12 div 3 =", calculate(12, 3, "div"))
    print(" 7 mul 6 =", calculate(7, 6, "mul"))
    try:
        calculate(1, 0, "div")
    except ValueError as e:
        print(" 1 div 0 → refused:", e)
