from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_404_NOT_FOUND,
	HTTP_200_OK,
	HTTP_201_CREATED
)
from rest_framework.permissions import AllowAny

from accounts.models import Account
from transfers.models import Transfer
from .models import Transaction
from .serializers import TransactionSerializer
from utils.api_response import APIFailure, APISuccess
from utils.choices import Transaction as TransactionOptions
from deposits.models import Deposit
from .helpers import process_transaction
from services.paystack_service import PaystackService

class ListCreateTransactionsView(generics.ListCreateAPIView):
	"""
	GET transactions/
	POST transactions/
	"""
	queryset = Transaction.objects.all()
	serializer_class = TransactionSerializer

	def get(self, request, type_of_account, *args, **kwargs):
		if type_of_account == 'deposits':
			type_of_account = 'deposit'
		type_of_account = getattr(Account, type_of_account.upper(), 10)
		account = get_object_or_404(Account, type_of_account=type_of_account, user=request.user)

		transactions = Transaction.objects.filter(account = account).order_by('-id')
		data = TransactionSerializer(transactions, many=True).data
		return APISuccess(data=data)
	
	def post(self, request, type_of_account, *args, **kwargs):
		type_of_transaction = getattr(TransactionOptions, request.data.get('type_of_transaction').title())
		transaction = TransactionSerializer(data=request.data, context=self.get_renderer_context())
		if transaction.is_valid():
			transaction = transaction.save()
			message, transaction = process_transaction(transaction)
			return APISuccess(message="Your transaction is processing", data=TransactionSerializer(transaction).data)

		return APIFailure(transaction.errors, status=HTTP_400_BAD_REQUEST)


def redirect_deposits(request):
    response = redirect('/api/v1/users/me/accounts/deposit/transactions/')
    return render
class InitializeTransaction(APIView):

	def post(self, request, *args, **kwargs):
		'''
		- Initializes an account.
		- payload:  'amount': 200,
				  'email': 'example@gmail.com'	
		- method: POST
		'''

		amount = request.data.get("amount", None)
		email = request.data.get("email", None)

		if amount and email:
			paystack = PaystackService()

			resp = paystack.initialize_transaction(amount, email)
			return Response(resp)

		return APIFailure(
				'Please provide both amount and email',
				HTTP_400_BAD_REQUEST
			)


class ResolveAccountNumber(APIView):

	def post(self, request, *args, **kwargs):
		'''
		- Verify an account number before creating a transfer recipient.
		- payload:  'account_number': 0001234567,
				  	'bank_code': '058'	
		- method: GET
		'''

		account_number = request.data.get("account_number", None)
		bank_code = request.data.get("bank_code", None)

		if account_number and bank_code:
			paystack = PaystackService()

			resp = paystack.resolve_account_number(account_number, bank_code)
			return Response(resp)

		return APIFailure(
				'Please provide both account_number and bank_code',
				HTTP_400_BAD_REQUEST
			)


class ChickenChangeView(APIView):

	def post(self, request, *args, **kwargs):
		'''
		- Add chicken change amount to an exisiting user's account
		- Payload: 'dest_account_id': 1,
					'amount'
		- Method: POST
		'''
		dest_account_id = request.data.get('dest_account_id', None)
		amount = int(request.data.get('amount', None))

		if not request.user.is_staff:
			return APIFailure('User must be a staff')

		if amount and dest_account_id and request.user.is_staff:
			dest_account = Account.objects.get(id=dest_account_id)
			agent_account = Account.objects.get(user=request.user, type_of_account=Account.WALLET)
			
			if dest_account.id == agent_account.id:
				return APIFailure("Deposits to own account is forbidden")

			dest_account.chicken_change_deposit(request.user, amount)
			return APISuccess(message=f"Your deposit to '{dest_account.user.full_name()}' was successful")

		return APIFailure(
				'Please provide both dest_account_id and amount',
			)			