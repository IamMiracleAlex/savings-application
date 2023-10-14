from rest_framework.response import Response
import hashlib
import hmac
import json
from rest_framework.permissions import AllowAny
from users.models import CustomUser
from services.paystack_service import PAYSTACK_KEY
from .models import Transaction, TransactionOptions
from .helpers import create_fund_source
from utils.api_response import APIFailure, APISuccess
from rest_framework.views import APIView

class PaystackWebhook(APIView):
	permission_classes = (AllowAny,)
	def post(self, request, format=None):
		response, computed_hmac = auth_webhook(request)
		if (request.headers.get('X-Paystack-Signature') == computed_hmac):
			if (response['event'] == 'charge.success'):
				deposit = Transaction.objects.filter(reference=response['data']['reference']).first()
				if deposit:
					deposit.succeed()
				else:
					user = CustomUser.objects.filter(email__iexact=response['data']['customer']['email']).first()
					if user:
						create_fund_source(user.id, response['data']['reference'], (response['data']['amount']/100))
						
			if (response['event'] == 'transfer.success'):
				withdraw = Transaction.objects.filter(reference=response['data']['reference']).first()
				if withdraw:
					withdraw.succeed()
			if (response['event'] == 'transfer.failed'):
				withdraw = Transaction.objects.filter(reference=response['data']['reference']).first()
				if withdraw:
					withdraw.reject()

		return Response({'message': 'message'})

class MonnifyWebhook(APIView):
	permission_classes = (AllowAny,)
	def post(self, request, format=None):
		response = request.data
		if (response['transactionHash'] == auth_monnify(response)) and (response['paymentStatus'] == 'PAID'):
			user = CustomUser.objects.filter(email=response['customer']['email']).first()
			if user:
				account = Account.objects.get(user=user, type_of_account=Account.WALLET)
				deposit = Deposit.objects.create(
					account = account,
					amount = Decimal(response['amountPaid']),
					type_of_deposit = Deposit.BankTransfer,
				)
				deposit.succeed()
				if not user.account_activated:
					user.account_activated = True
					user.save()

		return Response({'message': 'message'})



def auth_monnify(response):
	transaction = '{}|{}|{}|{}|{}'.format(
		config('MONNIFY_SECRET'),
		response['paymentReference'],
		response['amountPaid'],
		response['paidOn'],
		response['transactionReference']
	)
	return hashlib.sha512(bytes(transaction, 'utf-8')).hexdigest()


def auth_webhook(request):
	json_body = json.loads(request.body)
	response = request.data
	computed_hmac = hmac.new(
		bytes(PAYSTACK_KEY, 'utf-8'),
		str.encode(request.body.decode('utf-8')),
		digestmod=hashlib.sha512
	).hexdigest()
	return response, computed_hmac