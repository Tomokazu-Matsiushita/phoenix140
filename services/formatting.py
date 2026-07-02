def yen(value) -> str:
    try:
        return f"¥{float(value):,.0f}"
    except Exception:
        return "¥0"
