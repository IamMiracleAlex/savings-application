from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from rest_framework.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_404_NOT_FOUND,
	HTTP_200_OK,
	HTTP_201_CREATED
)
from datetime import timedelta, date
from services.paystack_service import PaystackService
from accounts.models import Account
from utils.api_response import APIFailure, APISuccess
from celery import shared_task
from deposits.models import FundSource
from safelocks.models import SafeLock
# Create your views here.


class CreateSubscriptionsView(generics.CreateAPIView):
	"""
	POST subscriptions/
	"""
	queryset = Subscription.objects.all()
	serializer_class = SubscriptionSerializer

	def post(self, request, type_of_account, *args, **kwargs):
		serializer = SubscriptionSerializer(data=request.data, context=self.get_renderer_context())
		if serializer.is_valid():
			subscription = serializer.save()
			if request.data.get('safelock_id'):
				safelock = SafeLock.objects.get(id=request.data['safelock_id'], account = subscription.account)
				if safelock:
					safelock.subscription = subscription
					safelock.save()
			if (subscription.start_date == date.today()):
				activate_subscription.delay(subscription.id)
				subscription.set_next_paydate()
				subscription.save()
			return APISuccess(
				message = "Periodic debits has been activated on your account", 
				data = SubscriptionSerializer(subscription).data
			)
		return APIFailure(message=serializer.errors)


class RetrieveUpdateSubscriptionView(generics.RetrieveUpdateAPIView):
	"""
	PUT subscriptions/
	GET subscriptions/
	"""
	queryset = Subscription.objects.all()
	serializer_class = SubscriptionSerializer

	def get(self, request, type_of_account, *args, **kwargs):
		type_of_account = getattr(Account, type_of_account.upper(), 10)
		account = Account.objects.get(user=request.user, type_of_account=type_of_account)
		subscriptions = Subscription.objects.filter(account=account)
		serializer = SubscriptionSerializer(subscriptions, many=True)
		return APISuccess(data=serializer.data)
	
	def put(self, request, type_of_account, *args, **kwargs):
		type_of_account = getattr(Account, type_of_account.upper(), 10)
		account = Account.objects.get(user=request.user, type_of_account=type_of_account)
		subscription = Subscription.objects.filter(account=account, id=request.data['id']).last()
		if subscription:
			serializer = SubscriptionSerializer()
			updated_sub = serializer.update(subscription, request.data)
			updated_sub.save()
			return APISuccess(message='Direct debit has beeen successfully updated',data=SubscriptionSerializer(updated_sub).data)
		return APISuccess({})

class EnableSubscription(APIView):
	def post(self, request, type_of_account, format=None):
		type_of_account = getattr(Account, type_of_account.upper(), 10)
		account = Account.objects.get(
			user=request.user,
			type_of_account=type_of_account
		)
		subscription = Subscription.objects.filter(account=account, id=request.data['id']).last()
		if subscription:
			subscription.enable()
			subscription.set_next_paydate()
			subscription.save()
			return APISuccess(message="Your Subscription has been enabled", data=SubscriptionSerializer(subscription).data)
		return APIFailure(message="User does not have subscription with id: {}".format(request.data['id']), status=HTTP_404_NOT_FOUND)

class DisableSubscription(APIView):
	def post(self, request, type_of_account, format=None):
		type_of_account = getattr(Account, type_of_account.upper(), 10)
		account = Account.objects.get(
			user=request.user,
			type_of_account=type_of_account
		)
		subscription = Subscription.objects.filter(account=account, id=request.data['id']).last()
		if subscription:
			subscription.disable()
			return APISuccess(message="Your Subscription has been disabled", data=SubscriptionSerializer(subscription).data)
		return APIFailure(message="User does not have subscription with id: {}".format(request.data['id']), status=HTTP_404_NOT_FOUND)

@shared_task
def activate_subscription(subscription_id):
	subscription = Subscription.objects.get(id=subscription_id)
	deposit = subscription.create_deposit()
	fund_source = FundSource.objects.get(id=deposit.data['fund_source_id'])

	paystack = PaystackService()
	response = paystack.charge_card(deposit, fund_source)
	if (response['status'] == True):
		if (response['data']['status'] == 'success'):
			deposit.succeed()
			safelock = subscription.safelock
			if safelock:
				safelock.amount += deposit.amount
				safelock.save()
			return True
	deposit.reject()