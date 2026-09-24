def apply_discount(amount: float, percent: float) -> float:
    # Obvious bug: adds instead of subtracts.
    return amount + (amount * percent / 100.0)
