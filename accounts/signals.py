from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from .models import Account

logger = logging.getLogger("project")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_account_handler(sender, instance, created, **kwargs):
    if created:
        instance.populate_accounts()
        instance.create_kyc()