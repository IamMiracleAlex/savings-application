from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from celery import shared_task


class GsuiteService:

    def send_activation_mail(context):
        subject = "{}, Welcome to Savest".format(context['name'])
        template = 'emails/activate_email.html'
        sender.delay(subject, template, context, context['email'])

    def send_safelock_maturity_mail(context):
        subject = "{}, {} has been credited to your SaVests Wallet".format(context['name'], context['total'])
        template = 'emails/safelock_maturity.html'
        sender.delay(subject, template, context, context['email'])

    def send_transaction_failed_mail(context):
        subject = "{} Failed".format(context['transaction_type'])
        template = 'emails/transaction_failed.html'
        sender.delay(subject, template, context, context['email'])

    def send_transaction_success_mail(context):
        subject = "{} Success".format(context['transaction_type'])
        template = 'emails/transaction_success.html'
        sender.delay(subject, template, context, context['email'])




@shared_task
def sender(subject, template, context, dest):
	html_message = render_to_string(template, context)

	send_mail(subject, settings.DEFAULT_FROM_EMAIL, [dest], html_message=html_message, fail_silently=False,)    