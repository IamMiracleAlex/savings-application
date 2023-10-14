from decimal import Decimal
from datetime import date

from django.shortcuts import get_object_or_404

from rest_framework import serializers

from accounts.models import Account
from .models import Transaction
from utils.api_response import APIFailure
from utils.choices import Transaction as TransactionOptions
from deposits.models import FundSource
from withdraws.models import Beneficiary
from users.models import CustomUser
from services.paystack_service import PaystackService
from .helpers import create_deposit


WITHDRAWAL_DATES = ["2020-03-28", "2020-06-28", "2020-09-28", "2020-12-28"]


class TransactionSerializer(serializers.ModelSerializer):
	type_of_transaction = serializers.CharField(source='get_type_of_transaction_display')
	amount = serializers.IntegerField(required=True)
	fee = serializers.IntegerField(required=False, read_only=True)
	balance_after_transaction = serializers.IntegerField(required=False, read_only=True)
	memo = serializers.CharField(required=False)
	fund_source_id = serializers.IntegerField(required=False, write_only=True)
	beneficiary_id = serializers.IntegerField(required=False, write_only=True)
	dest_account_id = serializers.IntegerField(required=False)
	customer_id = serializers.CharField(required=False)
	name_of_biller = serializers.CharField(required=False)
	type_of_biller = serializers.ChoiceField(
		required=False,
		choices= (
			('Airtime', 'Airtime'),
			('Internet', 'Internet'),
			('CableTV', 'CableTV'),
			('TollPayment', 'TollPayment'),
			('Electricity', 'Electricity')
		)
	)
	fund_source_type = serializers.ChoiceField(
		required=False,
		choices = (
		('Wallet', 'Wallet'),
		('Card', 'Card'),
	)
	)
	status = serializers.CharField(source='get_status_display', read_only=True)
	data = serializers.SerializerMethodField(source='get_data', read_only=True)
	type_of_account = serializers.SerializerMethodField(read_only=True)
	type_of_dest_account = serializers.SerializerMethodField(read_only=True, source='get_type_of_dest_account')

	def validate(self, data):
		type_of_account = getattr(
			Account, 
			self.context['view'].kwargs['type_of_account'].upper(), 
			10
		)
		data['account'] = get_object_or_404(Account, user=self.context['request'].user, type_of_account=type_of_account)
		data['type_of_transaction'] = getattr(TransactionOptions, data['get_type_of_transaction_display'].title())
		
		if (self.initial_data['type_of_transaction'] == 'deposit'):
			fund_source = FundSource.objects.filter(id=data.get('fund_source_id'), user=self.context['request'].user).first()
			if not fund_source:
				raise serializers.ValidationError("The deposit fund source is invalid")

		if (self.initial_data['type_of_transaction'] == 'transfer'):
			dest_account = Account.objects.filter(id=data.get('dest_account_id')).first()
			if not dest_account:
				raise serializers.ValidationError("The destination account specified is invalid")
			data['dest_account'] = dest_account
			data = validate_transfer(data['account'], dest_account, data)

		if (self.initial_data['type_of_transaction'] == 'withdraw'):
			if (data['account'].type_of_account != Account.WALLET):
				raise serializers.ValidationError("Invalid account transaction")
			beneficiary = self.context['request'].user.default_withdraw_beneficiary
			if not beneficiary:
				raise serializers.ValidationError("You have not set a valid withdrawal beneficiary")
			data['beneficiary_id'] = beneficiary.id
		
		if (self.initial_data['type_of_transaction'] == 'payment'):
			if (data['account'].type_of_account != Account.WALLET):
				raise serializers.ValidationError("Invalid account transaction")
			data['user'] = self.context['request'].user
			data = validate_payment(data)
		return data

	def get_data(self, obj):
		return obj.data

	def get_type_of_account(self, obj):
		return obj.account.get_type_of_account_display()

	def get_type_of_dest_account(self, obj):
		if obj.dest_account:
			return obj.dest_account.get_type_of_account_display()
		return None

	def validate_amount(self, value):
		account = Account.objects.get(user=self.context['request'].user, type_of_account=Account.WALLET)
		if (self.initial_data['type_of_transaction'] == 'deposit' and value < 100):
			raise serializers.ValidationError("Minimum deposit of NGN 100")
		if (self.initial_data['type_of_transaction'] == 'withdraw'):
			if (value < 2000):
				raise serializers.ValidationError("Minimum withdrawal of NGN 2000")
		if ((self.initial_data['type_of_transaction'] == 'withdraw') and (value > account.balance)):
			raise serializers.ValidationError("Insufficient Balance")
		return value

	def create(self, validated_data):
		account  = Account.objects.get(id=validated_data['account'].id)
		transaction = Transaction.objects.create(
			account = account,
			type_of_transaction = validated_data['type_of_transaction'],
			amount = validated_data['amount'],
			fee = validated_data.get('fee', 0),
			balance_after_transaction = validated_data['account'].balance,
			memo = validated_data.get('memo')
		)
		transaction.data = {}
		if self.initial_data['type_of_transaction'] == 'deposit':
			transaction.data['fund_source_id'] = validated_data['fund_source_id']
			transaction.data['type_of_deposit'] = 'QuickSave'

		if self.initial_data['type_of_transaction'] == 'withdraw':
			transaction.data['beneficiary_id'] = validated_data['beneficiary_id']

		if self.initial_data['type_of_transaction'] == 'payment':
			transaction.data['customer_id'] = validated_data['customer_id']
			transaction.data['name_of_biller'] = validated_data['name_of_biller']
			transaction.data['type_of_biller'] = validated_data['type_of_biller']
			transaction.data['fund_source_type'] = validated_data['fund_source_type']
			transaction.data['fund_source_id'] = validated_data['fund_source_id']

		if self.initial_data['type_of_transaction'] == 'transfer':
			transaction.dest_account_id = validated_data['dest_account_id']
			transaction.dest_account = validated_data['dest_account']
			transaction.data['transfer_type'] = validated_data['transfer_type']
		transaction.save()
		transaction.process()
		return transaction

	class Meta:
		model = Transaction
		fields = ('id', 'account_id', 'dest_account_id','type_of_account', 'type_of_dest_account', 'type_of_transaction', 'status', 'reference', 'amount', 'fee', 'total', 'balance_after_transaction', 
					'memo', 'data', 'reference', 'created_at', 'updated_at', 'fund_source_id', 'beneficiary_id', 
					'customer_id', 'name_of_biller', 'type_of_biller', 'fund_source_type')


def validate_transfer(src_account, dest_account, data):
	if (src_account.type_of_account == Account.DIRECT):
		today = date.today().strftime('%Y-%m-%d')
		if today not in WITHDRAWAL_DATES:
			data['fee'] = Decimal(data['amount'] * 0.05)
		else:
			data['fee'] = Decimal(0)
	else:
		data['fee'] = Decimal(0)
	
	if (src_account.type_of_account == Account.WALLET) and (dest_account.type_of_account == Account.WALLET):
		data['transfer_type'] = 'PeerToPeer'
	else:
		data['transfer_type'] = 'InternalTransfer'
	if (src_account == dest_account):
		raise serializers.ValidationError("Invalid transaction")
	if ((data['amount'] + data['fee']) > src_account.balance):
		raise serializers.ValidationError("Insufficient Balance")
	return data

def validate_payment(data):
	account = Account.objects.get(user=data['user'], type_of_account=Account.WALLET)
	if not data['user'].account_activated:
		raise serializers.ValidationError("You have to activate your account before you can make payments.")
	if not (data.get('customer_id') and data.get('name_of_biller') and data.get('type_of_biller') and data.get('fund_source_type')):
		raise serializers.ValidationError("Customer ID, name of biller, type of biller, fund source type cannot be null")
	
	if (data['type_of_biller'].upper() == 'AIRTIME') or (data['type_of_biller'].upper() == 'INTERNET'):
		data['fee'] = Decimal(0)
	else:
		data['fee'] = Decimal(100)

	if data['fund_source_type'] == 'Wallet':
		data['fund_source_id'] = None
		if ((data['amount'] + data['fee']) > account.balance):
			raise serializers.ValidationError("Insufficient Balance")
	else:
		fundsource = FundSource.objects.filter(id=data['fund_source_id'], user=data['user']).last()
		if not fundsource:
			raise serializers.ValidationError("Invalid card selected")
		_, deposit = create_deposit(account, data['amount'], fundsource)
		if (deposit.status == TransactionOptions.FAILED):
			raise serializers.ValidationError("Unable to debit card")
	return data

