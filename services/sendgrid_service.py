# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To
from decouple import config
from celery import shared_task



class SendgridService:
	def send_activation_mail(context):
		subject = "{}, Welcome to Savest".format(context['name'])
		template = 'd-d09d0c4678ab4579b0cd90876c488249'
		send_mail.delay(subject, template, context, context['email'])

	def send_safelock_maturity_mail(context):
		subject = "{}, {} has been credited to your SaVests Wallet".format(context['name'], context['total'])
		context['subject'] = subject
		template = 'd-ebb545022ded43738d9a247a52fd2955'
		send_mail.delay(subject, template, context, context['email'])

	def send_transaction_failed_mail(context):
		subject = "{} Failed".format(context['transaction_type'])
		context['subject'] = subject
		template = 'd-10514021e58c4b60a738fc47b8a608d5'
		send_mail.delay(subject, template, context, context['email'])

	def send_transaction_success_mail(context):
		subject = "{} Success".format(context['transaction_type'])
		context['subject'] = subject
		template = 'd-0e6a7a7d5080412b911de4657fd22b43'
		send_mail.delay(subject, template, context, context['email'])

@shared_task
def send_mail(subject, template, context, dest):
	message = Mail(
		from_email=From('contact@savests.com', 'SaVests'),
		to_emails=dest,
		html_content='<strong>Hello, from SaVests</strong>')
	message.dynamic_template_data = context
	message.template_id = template
	try:
		sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
		response = sg.send(message)
		
	except Exception as e:
		pass
