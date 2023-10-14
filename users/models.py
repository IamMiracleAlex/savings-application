from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from utils.helpers import generate_unique_id
from .managers import CustomUserManager
from accounts.models import Account
from kyc_profiles.models import KYCProfile

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    refer_code = models.CharField(
        max_length=15,
        unique=True,
        editable=False,
    )
    public_id = models.CharField(max_length=15, unique=True, editable=False)
    referer = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='referrals'
    )
    account_activated = models.BooleanField(default=False)
    paid_referer_bonus = models.BooleanField(default=False)
    account_number = models.CharField(max_length=15, editable=False, null=True, blank=True)
    account_bank_name = models.CharField(max_length=50, null=True, blank=True)
    default_deposit_fund_source = models.OneToOneField('deposits.FundSource', on_delete=models.SET_NULL, null=True, blank=True)
    default_withdraw_beneficiary = models.OneToOneField('withdraws.Beneficiary', on_delete=models.SET_NULL, null=True, blank=True)
    send_notifications = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def wallet_balance(self):
        return self.account_set.get(type_of_account=Account.WALLET).balance

    def direct_balance(self):
        return self.account_set.get(type_of_account=Account.DIRECT).balance
    
    def target_balance(self):
        return self.account_set.get(type_of_account=Account.DEPOSIT).balance
    
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.refer_code = generate_unique_id(CustomUser, 'refer_code')
            self.public_id = generate_unique_id(CustomUser, 'public_id')
        super(CustomUser, self).save(*args, **kwargs)

    def populate_accounts(self):
        for i in range(3):
            account = Account(
                user=self,
                type_of_account=i
                )
            if i != Account.WALLET:
                account.interest_active = True
            account.save()
    
    def create_kyc(self):
        KYCProfile.objects.create(user = self)

    def kyc_level(self):
        from kyc_profiles.models import KYCProfile
        return KYCProfile.objects.get(user=self).verification_level
        




class UserMetric(CustomUser):

    class Meta:
        proxy = True
        verbose_name_plural = 'User Metrics'  



class MassNotification(models.Model):    
    title = models.CharField(max_length=100)
    message = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, related_name='notifications_update')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Mass Notification"
