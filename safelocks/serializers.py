from .models import *
from rest_framework import serializers
from datetime import date, timedelta
from accounts.models import Account
from accounts.serializers import AccountSerializer
from subscriptions.serializers import Subscription, SubscriptionSerializer

class SafeLockSerializer(serializers.ModelSerializer):
	name = serializers.CharField(required=True)
	reference = serializers.CharField(required=True, write_only=True)
	amount = serializers.IntegerField(required=True)
	target_goal = serializers.IntegerField(required=True)
	maturity_date = serializers.DateField(required=True, format="%Y-%m-%d")
	transfer_from = serializers.ChoiceField(
		required=True,
		choices= (
			('wallet','wallet'),
			('card','card')
		),
		write_only=True)
	category = serializers.CharField(
		required=True,
		write_only=True)
	account = serializers.SerializerMethodField(read_only=True)
	subscription = serializers.SerializerMethodField(read_only=True)

	def get_account(self, obj):
		ac = Account.objects.get(id=obj.account_id)
		account = AccountSerializer(ac).data
		return account

	def get_subscription(self, obj):
		account = Account.objects.get(id=obj.account_id)
		subscription = Subscription.objects.filter(id=obj.subscription_id).last()
		if subscription:
			return SubscriptionSerializer(subscription).data
		return {}

	def validate_maturity_date(self, value):
		if (date.today() + timedelta(days=30)) > value:
			raise serializers.ValidationError('Maturity date must exceed at least 30 days in the future')
		return value

	def validate_amount(self, value):
		if value < 1000:
			raise serializers.ValidationError("Minimum Term Deposit of 1000 Naira")
		return value

	def validate(self, data):
		user = self.context['request'].user
		from_account = Account.objects.get(
			user=user,
			type_of_account = Account.WALLET
		)
		data['account'] = Account.objects.get(
			user=user,
			type_of_account = Account.DEPOSIT
		)
		if (data['transfer_from'] == 'wallet') and (from_account.balance < data['amount']):
			raise serializers.ValidationError("Insufficient Balance")
		
		if (data['transfer_from'] == 'card') and not (user.default_deposit_fund_source):
			raise serializers.ValidationError("Please add a card")
		
		return data
		
	def create(self, validated_data):
		safelock= SafeLock.objects.create(
			name = validated_data['name'],
			account = validated_data['account'],
			amount = validated_data['amount'],
			target_goal = validated_data['target_goal'],
			maturity_date = validated_data['maturity_date'],
			category = getattr(SafeLock ,validated_data['category'])
		)
		return safelock

	class Meta:
		model = SafeLock
		fields = ('id', 'name', 'amount', 'target_goal', 'reference', 'subscription', 'subscription_id', 'transfer_from', 'interest', 'maturity_date', 'category', 'account', 'is_active', 'created_at', 'updated_at')
