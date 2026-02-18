from decimal import Decimal, ROUND_HALF_UP

class Money:
    """
    Encapsulates currency logic to ensure consistent precision and rounding across the application.
    """
    
    @staticmethod
    def quantize(amount: Decimal | float | str | int) -> Decimal:
        """
        Converts any number to a Decimal with exactly 2 decimal places, 
        using standard financial rounding (ROUND_HALF_UP).
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def to_string(amount: Decimal) -> str:
        """
        Formats a Decimal as a string for JSON serialization, ensuring 2 decimal places.
        """
        return f"{amount:.2f}"
