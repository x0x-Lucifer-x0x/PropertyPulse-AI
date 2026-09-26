def calculate_affordability(
    property_price: float,
    down_payment: float,
    interest_rate: float,
    tenure_years: int,
) -> dict:
    """Standard reducing-balance EMI calculation."""
    loan_amount = max(0.0, property_price - down_payment)
    if loan_amount == 0 or tenure_years <= 0:
        return {
            "loan_amount": loan_amount,
            "monthly_emi": 0.0,
            "total_interest": 0.0,
            "total_payment": loan_amount,
        }

    monthly_rate = (interest_rate / 100) / 12
    months = tenure_years * 12

    if monthly_rate == 0:
        emi = loan_amount / months
    else:
        emi = (
            loan_amount
            * monthly_rate
            * (1 + monthly_rate) ** months
            / ((1 + monthly_rate) ** months - 1)
        )

    total_payment = emi * months
    total_interest = total_payment - loan_amount

    return {
        "loan_amount": round(loan_amount, 2),
        "monthly_emi": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
    }
