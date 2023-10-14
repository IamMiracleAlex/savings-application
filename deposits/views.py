import hashlib
import hmac
import json
from decimal import Decimal

from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_404_NOT_FOUND,
	HTTP_200_OK,
	HTTP_201_CREATED
)

from celery import shared_task
from decouple import config

from .models import Deposit, FundSource
from accounts.models import Account
from transfers.models import Transfer
from .serializers import AddCardSerializer, FundSourceSerializer
from services.paystack_service import PaystackService
from utils.api_response import APIFailure, APISuccess
from users.models import CustomUser
from services.paystack_service import PAYSTACK_KEY
from utils.choices import Transaction as TransactionOptions
from subscriptions.models import Subscription
from withdraws.models import Withdraw
from services.pusher_service import PusherService
from transactions.models import Transaction, TransactionOptions
from django.utils import timezone




class PaystackWebhook(APIView):
	permission_classes = (AllowAny,)
	def post(self, request, format=None):
		response, computed_hmac = auth_webhook(request)
		if (request.headers.get('X-Paystack-Signature') == computed_hmac):
			if (response['event'] == 'charge.success'):
				deposit = Transaction.objects.filter(reference=response['data']['reference'], type_of_transaction=TransactionOptions.Deposit).first()
				if deposit:
					pass
					# deposit.succeed()
				else:
					user = CustomUser.objects.filter(email__iexact=response['data']['customer']['email']).first()
					if user:
						create_fund_source(user.id, response['data']['reference'], (response['data']['amount']/100))
						
			if (response['event'] == 'transfer.success'):
				withdraw = Transaction.objects.filter(reference=response['data']['reason'], type_of_transaction=TransactionOptions.Withdraw).first()
				if withdraw:
					withdraw.succeed()
			if (response['event'] == 'transfer.failed'):
				withdraw = Transaction.objects.filter(reference=response['data']['reason'], type_of_transaction=TransactionOptions.Withdraw).first()
				if withdraw:
					withdraw.reject()

		return Response({'message': 'message'})

class MonnifyWebhook(APIView):
	permission_classes = (AllowAny,)
	def post(self, request, format=None):
		response = request.data
		if (response['transactionHash'] == auth_monnify(response)) and (response['paymentStatus'] == 'PAID'):
			user = CustomUser.objects.filter(email__iexact=response['customer']['email']).first()
			if user:
				account = Account.objects.get(user=user, type_of_account=Account.WALLET)
				deposit, _ = Transaction.objects.get_or_create(
					account = account,
					amount = Decimal(response['amountPaid']),
					type_of_transaction = TransactionOptions.Deposit,
					reference = response['transactionReference']
				)
				deposit.data = {}
				deposit.data['type_of_deposit'] = 'BankTransfer'
				deposit.data['account_details'] = response['accountDetails']
				deposit.save()
				deposit.process()
				deposit.succeed()
				if not user.account_activated:
					user.account_activated = True
					user.save()

		return Response({'message': 'message'})


class PaystackAddCard(generics.CreateAPIView):
	serializer_class = AddCardSerializer

	def post(self, request, *args, **kwargs):
		data = AddCardSerializer(
			data=request.data,
			context=self.get_renderer_context()
		)

		if data.is_valid():
			create_fund_source(request.user.id, request.data['reference'], request.data['amount'])  
			return APISuccess(message = 'Processing card payment. Card would be added shortly if transaction was successful')  
		return APIFailure(message=data.errors)  

class RetrieveFundSourceView(generics.RetrieveAPIView):
	"""
	GET fund_source/
	"""
	queryset = FundSource.objects.all()
	serializer_class = FundSourceSerializer

	def get(self, request, *args, **kwargs):
		fund_sources = FundSource.objects.filter(user=request.user, is_active=True)
		serializer = FundSourceSerializer(fund_sources, many=True)
		return APISuccess(data=serializer.data)
	

class ChangeDefaultFundSource(APIView):
	def post(self, request, format=None):
		user = request.user
		fund_source = FundSource.objects.filter(user=user, id=request.data['fund_source_id']).first()
		if not fund_source:
			return APIFailure(message='Fund Source does not exist')
		user.default_deposit_fund_source = fund_source
		account = Account.objects.get(user=user, type_of_account=Account.DIRECT)
		subs = Subscription.objects.filter(account=account)
		for sub in subs:
			sub.fund_source = fund_source
			sub.save()
		user.save()
		return APISuccess(message="Successfully set default fund source")

def auth_webhook(request):
	json_body = json.loads(request.body)
	response = request.data
	computed_hmac = hmac.new(
		bytes(PAYSTACK_KEY, 'utf-8'),
		str.encode(request.body.decode('utf-8')),
		digestmod=hashlib.sha512
	).hexdigest()
	return response, computed_hmac

def auth_monnify(response):
	transaction = '{}|{}|{}|{}|{}'.format(
		config('MONNIFY_SECRET'),
		response['paymentReference'],
		response['amountPaid'],
		response['paidOn'],
		response['transactionReference']
	)
	return hashlib.sha512(bytes(transaction, 'utf-8')).hexdigest()

@shared_task
def create_fund_source(user_id, reference, amount):
	paystack = PaystackService()
	user = CustomUser.objects.get(id=user_id)
	response = paystack.verify_transaction(reference)
	if response.get('data') and response['data']['status'] == 'success':
		data = response['data']['authorization']
				
		account = Account.objects.get(
			user=user,
			type_of_account=Account.WALLET
		)

		fund_source, _ = FundSource.objects.get_or_create(
			user = user,
			last4 = data['last4'],
			bank_name = data['bank'],
			exp_month = data['exp_month'],
			exp_year = data['exp_year'],
			card_type = data['card_type'],
			is_active = True
		)
		
		fund_source.auth_code = data['authorization_code']
		fund_source.save()

		similar_cards = FundSource.objects.filter(last4 = data['last4'], bank_name = data['bank'], exp_month = data['exp_month'], exp_year = data['exp_year'])

		similar_cards = FundSource.objects.filter(last4=fund_source.last4, bank_name=fund_source.bank_name, exp_month=fund_source.exp_month, exp_year=fund_source.exp_year)
		if similar_cards.count() >= 2:
			for card in similar_cards:
				user = card.user
				user.is_active=False
				user.save()
			user.is_active=False
			user.save()


		
		from services.pusher_service import PusherService
		pusher = PusherService()
		pusher.add_card(fund_source)

		deposit, _ = Transaction.objects.get_or_create(
			reference = reference,
			account = account,
			type_of_transaction= TransactionOptions.Deposit,
			amount = Decimal(amount)
		)
		deposit.data = {}
		deposit.data['fund_source_id'] = fund_source.id
		deposit.data['type_of_deposit'] = 'QuickSave'

		deposit.succeed()
		if user.default_deposit_fund_source is None:
			user.default_deposit_fund_source = fund_source
			user.save()
		if user.account_activated == False:
			user.account_activated = True
			user.save()


@shared_task
def paystack_deposit(deposit_id):
	paystack = PaystackService()
	deposit = Deposit.objects.get(id=deposit_id)
	response = paystack.charge_card(deposit, deposit.fund_source)
	if (response['status'] == True):
		if (response['data']['status'] == 'success'):
			deposit.succeed()
			pusher = PusherService()
			pusher.new_deposit(deposit)
			return response['message'], deposit
	deposit.reject()
	return response['message'], deposit

def create_referral_deposit(user):
	ReferralAdminUser = CustomUser.objects.get(id=config('ReferralUserID'))
	referer = user.referer
	referral_bonus = Decimal(config('ReferralBonusAmount'))
	if referer:
		if referer.is_staff or referer.referrals.filter(account_activated=True).count() >= 10:
			return
		if user.paid_referer_bonus:
			return

		from_account = Account.objects.get(type_of_account=Account.WALLET, user=ReferralAdminUser)
		to_account = Account.objects.get(type_of_account=Account.DEPOSIT, user=referer)
		# Credit Target Savings account
		from safelocks.models import SafeLock
		maturity_date = timezone.now() + timezone.timedelta(days=31)
		safelock = SafeLock.objects.filter(account=to_account, name="{} Personal Savings".format(to_account.user.first_name), is_active=True).first()
		if not safelock:
			safelock = SafeLock.objects.create(
				account=to_account, 
				name="{} Personal Savings".format(to_account.user.first_name), 
				maturity_date=(timezone.now() + timezone.timedelta(days=31)),
				is_active=True
			)
		transfer = Transaction.objects.create(
			account=from_account,
			dest_account=safelock.account,
			amount = referral_bonus,
			type_of_transaction = TransactionOptions.Transfer,
			memo = '{} earned referring {}'.format(referral_bonus, user.first_name) 
		)
		transfer.data = {}
		transfer.data['transfer_type'] = 'ReferralBonus'
		transfer.save()
		transfer.process()
		transfer.succeed()
		safelock.amount = Decimal(safelock.amount) + Decimal(referral_bonus)
		safelock.save()
		user.paid_referer_bonus = True
		user.save()