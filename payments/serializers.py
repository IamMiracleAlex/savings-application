from rest_framework import serializers
from .models import Payment
from accounts.models import Account
from deposits.models import Deposit
from services.paystack_service import PaystackService
from services.pusher_service import PusherService
from django.shortcuts import get_object_or_404
from utils.choices import Transaction


class PaymentSerializer(serializers.ModelSerializer):
	amount = serializers.IntegerField(required=True)
	customer_id = serializers.CharField(required=True)
	name_of_biller = serializers.CharField(required=True)
	type_of_biller = serializers.ChoiceField(
		required=True,
		choices= (
			('Airtime', 'Airtime'),
			('CableTV', 'CableTV'),
			('TollPayment', 'TollPayment'),
			('Electricity', 'Electricity')
		)
	)
	fund_source_type = serializers.ChoiceField(
		required=True,
		choices = (
		('Wallet', 'Wallet'),
		('Card', 'Card'),
	)
	)
	status = serializers.CharField(source='get_status_display', read_only=True)
	
	def validate(self, data):
		data['user'] = self.context['request'].user
		account = Account.objects.get(user=data['user'], type_of_account=Account.WALLET)
		if not data['user'].account_activated:
			raise serializers.ValidationError("You have to activate your account before you can make payments.")
		if data['fund_source_type'] == 'Wallet':
			data['fund_source'] = None
			if (data['amount'] > account.balance):
				raise serializers.ValidationError("Insufficient Balance")
		else:
			_, deposit = create_deposit(account, data['amount'])
			data['fund_source'] = data['user'].default_deposit_fund_source
			if (deposit.status == Transaction.FAILED):
				raise serializers.ValidationError("Unable to debit card")
		return data

	def create(self, validated_data):
		payment_obj = Payment.objects.create(
			user = validated_data['user'],
			customer_id = validated_data['customer_id'],
			name_of_biller = validated_data['name_of_biller'],
			type_of_biller = getattr(Payment, validated_data['type_of_biller']),
			fund_source = validated_data.get('fund_source'),
			fund_source_type = getattr(Payment, validated_data.get('fund_source_type')),
			amount = validated_data['amount']
		)
		return payment_obj


	class Meta:
		model = Payment
		fields = ('id', 'customer_id', 'name_of_biller', 'type_of_biller', 'amount', 'reference', 'status', 'fund_source_type', 'fund_source', 'created_at', 'updated_at')
		read_only = ('status',)

def create_deposit(account, amount):
	deposit = Deposit.objects.create(
				account = account,
				amount = amount,
				fund_source = account.user.default_deposit_fund_source,
				type_of_deposit = Deposit.QuickSave,
		)
	paystack = PaystackService()
	response = paystack.charge_card(deposit, deposit.fund_source)
	if (response['status'] == True):
		if (response['data']['status'] == 'success'):
			deposit.succeed()
			pusher = PusherService()
			pusher.new_deposit(deposit)
			return response['message'], deposit
	deposit.reject()
	return response['message'], deposit