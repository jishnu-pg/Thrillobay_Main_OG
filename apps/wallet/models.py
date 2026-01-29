from django.db import models
from apps.common.models import TimeStampedModel


class Wallet(TimeStampedModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, help_text="Related user")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Current balance")

    def __str__(self):
        return f"{self.user.username} - ₹{self.balance}"


class WalletTransaction(TimeStampedModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions", help_text="Related wallet")
    transaction_type = models.CharField(max_length=20, help_text="Type of transaction (credit/debit)")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Transaction amount")
    reference = models.CharField(max_length=100, blank=True, help_text="Transaction reference ID")

    def __str__(self):
        return f"{self.transaction_type.upper()} - ₹{self.amount} - {self.wallet.user.username}"
