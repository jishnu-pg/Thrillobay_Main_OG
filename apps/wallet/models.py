from django.db import models
from apps.common.models import TimeStampedModel


class Wallet(TimeStampedModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} - ₹{self.balance}"


class WalletTransaction(TimeStampedModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20)  # credit / debit
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.transaction_type.upper()} - ₹{self.amount} - {self.wallet.user.username}"
