import logging
from itertools import chain

from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_404_NOT_FOUND,
	HTTP_200_OK,
	HTTP_201_CREATED
)
from push_notifications.models import GCMDevice, APNSDevice
from celery import shared_task

from utils import APISuccess, APIFailure
from utils.helpers import AccountActivationTokenGenerator
from services.monnify_service import MonnifyService
from accounts.models import Account
from .serializers import *
from services.gsuite_service import GsuiteService



logger = logging.getLogger(__name__)



class LoginView(APIView):
	permission_classes = (AllowAny,)

	def post(self, request):
		phone_number = request.data.get("phone_number")
		password = request.data.get("password")
		if phone_number is None or password is None:
			return APIFailure(
				'Please provide both phone number and password',
				HTTP_400_BAD_REQUEST
			)
		user = authenticate(phone_number=phone_number, password=password)
		if not user:
			return APIFailure(
				'Invalid Credentials',
				HTTP_404_NOT_FOUND
			)
		token, _ = Token.objects.get_or_create(user=user)
		if request.data.get('registration_id'):
			register_user_device(request, user)
		json = UserSerializer(user).data
		json['token'] = token.key
		return APISuccess(
			'Login Successful',
			json,
		)

class LogoutView(APIView):
	def post(self, request):
		devices = chain(APNSDevice.objects.filter(user=request.user), GCMDevice.objects.filter(user=request.user))
		# for device in devices:
		# 	device.delete()
		return APISuccess('Logout Successful')


class SignUpView(APIView):
	permission_classes = (AllowAny,)

	def post(self, request, format='json'):
		serializer = UserSerializer(data=request.data)
		if serializer.is_valid():
			user = serializer.save()
			if user:
				token = Token.objects.create(user=user)
				json = serializer.data
				json['token'] = token.key
				if request.data.get('registration_id'):
					register_user_device(request, user)
				if request.data.get('amount_to_save'):
					referer = user.referer
					if referer and referer.is_staff:
						account = user.account_set.get(type_of_account=Account.WALLET)
						amount_to_save = int(request.data.get('amount_to_save'))
						if (amount_to_save > 0):
							account = account.chicken_change_deposit(referer, amount_to_save)
						json = {}
						json['total_users_registered'] = referer.referrals.count()
						send_sms_registration(user, account.balance)
						return  APISuccess(
							"User created Successfully with a balance of {}".format(account.balance),
							json,
							HTTP_201_CREATED
						)
				return APISuccess(
					'User created Successfully',
					json,
					HTTP_201_CREATED
				)
		return APIFailure(serializer.errors, HTTP_400_BAD_REQUEST)


class UsersDetailsView(generics.RetrieveUpdateDestroyAPIView):
	"""
	GET users/:id
	PUT users/:id
	"""
	queryset = CustomUser.objects.all()
	serializer_class = UserSerializer

	def get(self, request, *args, **kwargs):
		user = CustomUser.objects.get(id=request.user.id)
		return APISuccess(
			'Success',
			UserSerializer(user).data,
			HTTP_200_OK
		)

	def put(self, request, *args, **kwargs):
		serializer = UserSerializer(data=request.data, partial=True)
		if serializer.is_valid():
			updated_user = serializer.update(request.user, request.data)
			updated_user.save()
			return APISuccess(
				'Success',
				UserSerializer(updated_user).data,
				HTTP_200_OK
			)
		return APIFailure(message=serializer.errors)

class SendActivationEmail(APIView):
	def post(self, request):
		send_activate_email(request, request.user)
		return APISuccess('Email sent Successful')

class ActivateEmail(View):
	permission_classes = (AllowAny,)
	def get(self, request, uidb64, token, *args, **kwargs):
		account_activation_token = AccountActivationTokenGenerator()
		try:
			uid = force_text(urlsafe_base64_decode(uidb64))
			user = CustomUser.objects.get(id=uid)
		except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
			user = None
			logger.error('Error occured while trying to activate email')

		context = dict()

		if user.email_verified:
			context['message'] = 'Your email has already been verified'
			return render(request, 'account_activation.html', context)


		if user is not None and account_activation_token.check_token(user, token) and not user.email_verified:
	
			from services.pusher_service import PusherService
			pusher = PusherService()
			pusher.email_verified(user)
			if user.account_number is None:
				generate_account_number.delay(user.id)
			user.email_verified = True
			user.save()

			context['message'] = 'Email verification successful'
			return render(request, 'account_activation.html', context)
		else:
			context['message'] = 'Email verification failed'
			return render(request, 'account_activation.html', context)


class EnableNotifications(APIView):
	def post(self, request):
		user = request.user
		if request.data.get('registration_id'):
			register_user_device(request, user)
		user.send_notifications = True
		user.save()
		return APISuccess(message="Notifications have been enabled")
		
class DisableNotifications(APIView):
	def post(self, request):
		user = request.user
		user.send_notifications = False
		user.save()
		return APISuccess(message="Notifications have been disabled")
		

def send_activate_email(request, user):
	account_activation_token = AccountActivationTokenGenerator()
	context = {
		'name': user.first_name,
		'email': user.email,
		'domain': get_current_site(request).domain,
		'uid': urlsafe_base64_encode(force_bytes(user.id)),
		'token': account_activation_token.make_token(user),
	}
	GsuiteService.send_activation_mail(context)

def test_email(request):
	account_activation_token = AccountActivationTokenGenerator()
	user = CustomUser.objects.first()
	context = {
		'name': user.first_name,
		'email': user.email,
		'domain': get_current_site(request).domain,
		'uid': urlsafe_base64_encode(force_bytes(user.id)),
		'token': account_activation_token.make_token(user),
	}
	# return render(request, 'emails/activate_email.html', context=context)
	# return render(request, 'emails/transaction_failed.html', context=context)
	return render(request, 'emails/safelock_maturity.html', context=context)
	# return render(request, 'emails/transaction_success.html', context=context)


@shared_task
def generate_account_number(user_id):
	user = CustomUser.objects.get(id=user_id)
	monnify = MonnifyService()
	res = monnify.create_reserved_accounts(user)
	if (res['requestSuccessful'] == True):
		user.account_number = res['responseBody']['accountNumber']
		user.account_bank_name = res['responseBody']['bankName']
		user.save()
		return user

def register_user_device(request, user):
	if request.data.get("os") == "android":
		device, new_token = GCMDevice.objects.get_or_create(
			cloud_message_type='FCM', 
			registration_id=request.data.get('registration_id'))
			
	if request.data.get("os") == "ios":
		device, new_token = APNSDevice.objects.get_or_create(registration_id=request.data.get('registration_id'))

	device.user=user
	device.active=True
	device.save()
	device.send_message("Hi {}, You just logged in".format(user.first_name), extra={"title": "Login Successful"})
	return True

def send_sms_registration(user, amount):
	from services.sms_service import BulkSMSService
	sms = BulkSMSService()
	body = "Hello {}\nYou have NGN{} saved in your SaVests wallet. Download SaVests wallet to start saving.\nhttps://savests.com/download".format(user.first_name, amount)
	return sms.send_sms(user, body)