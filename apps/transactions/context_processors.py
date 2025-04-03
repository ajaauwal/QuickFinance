# apps/transactions/context_processors.py

from .models import Wallet

def wallet_balance(request):
    """
    Context processor to get the wallet balance of the authenticated user.
    """
    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(user=request.user).first()
        balance = wallet.balance if wallet else 0
        return {'wallet_balance': balance}
    return {'wallet_balance': 0}
