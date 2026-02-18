from decimal import Decimal, ROUND_HALF_UP
#I want to centralize the currency logic here, and I want to use it in the reservations service
#also if i want to change the currency in the future, i can do it here, also the rounding rules will need to be changed in only one file, here, and not 10 files
class Money:

    
    @staticmethod
    def quantize(amount: Decimal | float | str | int) -> Decimal:

        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def to_string(amount: Decimal) -> str:
        return f"{amount:.2f}"
