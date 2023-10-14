from django.db import models
from django.conf import settings

class FundSource(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    last4 = models.CharField(max_length=50)
    bank_name = models.CharField(null=True, blank=True, max_length=50)
    card_type = models.CharField(max_length=50)
    exp_month = models.CharField(max_length=50)
    exp_year = models.CharField(max_length=50)
    auth_code = models.CharField(max_length=50, unique=False) # CHANGE THIS
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} {}".format(self.last4, self.bank_name)

