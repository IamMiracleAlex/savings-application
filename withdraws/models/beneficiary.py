from django.db import models
from django.conf import settings

class Beneficiary(models.Model):
    SavestUser, BankAccount = range(2)
    BENEFICIARY_TYPES = (
        (SavestUser, 'SavestUser'),
        (BankAccount, 'BankAccount'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    uid = models.CharField(null=True, blank=True, max_length=50)
    uid2 = models.CharField(null=True, blank=True, max_length=50)
    type_of_beneficiary = models.PositiveSmallIntegerField(
        choices=BENEFICIARY_TYPES,
        default=BankAccount
    )
    recipient_code = models.CharField(null=True, blank=True, max_length=150, unique=False) # DISCUSS THIS WITH BUSINESS
    recipient_name = models.CharField(null=True, blank=True, max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return "{}: {}'s beneficiary".format(self.uid, self.user)
