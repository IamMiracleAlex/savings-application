from rest_framework import serializers
from .models import Subscription
from accounts.models import Account
from accounts.serializers import AccountSerializer
from datetime import date
from django.shortcuts import get_object_or_404


class SubscriptionSerializer(serializers.ModelSerializer):
	amount = serializers.IntegerField(required=True)
	start_date = serializers.DateField(required=True, format="%Y-%m-%d")
	interval = serializers.CharField(required=True, source='get_interval_display')
	account = serializers.SerializerMethodField(read_only=True)
	safelock_id = serializers.IntegerField(required=False, write_only=True)

	def validate(self, data):
		type_of_account = getattr(
			Account, 
			self.context['view'].kwargs['type_of_account'].upper(), 
			10
		)
		account = get_object_or_404(Account, user=self.context['request'].user, type_of_account=type_of_account)
		data['account'] = account
		if type_of_account == Account.DIRECT:
			initial_sub = Subscription.objects.filter(account=account).last()
			if initial_sub:
				raise serializers.ValidationError('Subscription already exists for user')
		data['fund_source'] = account.user.default_deposit_fund_source
		if not data['fund_source']:
			raise serializers.ValidationError("Please add a card to proceed")
		return data
	
	def validate_start_date(self, value):
		if date.today() > value:
			raise serializers.ValidationError('Start Date cannot be in the past')
		return value

	def create(self, validated_data):
		subscription_obj, new_obj = Subscription.objects.get_or_create(
			name = validated_data['name'],
			account = validated_data['account'],
			amount = validated_data['amount'],
			fund_source = validated_data['fund_source'],
			interval = getattr(Subscription, validated_data['get_interval_display'].upper()),
			start_date = validated_data['start_date'],
			previous_paydate = validated_data['start_date'],
			next_paydate = validated_data['start_date'],
			is_active = True
		)
		return subscription_obj

	def update(self, instance, validated_data):
		instance.amount = validated_data.get('amount', instance.amount)
		new_interval = validated_data.get('interval')
		if new_interval:
			instance.interval = getattr(Subscription, new_interval.upper())
		instance.save()
		return instance

	def get_account(self, obj):
		ac = Account.objects.get(id=obj.account_id)
		account = AccountSerializer(ac).data
		return account

		
	class Meta:
		model = Subscription
		fields = ('id', 'name', 'account', 'amount', 'interval', 'is_active', 'start_date', 'previous_paydate', 'next_paydate', 'created_at', 'updated_at', 'safelock_id')
