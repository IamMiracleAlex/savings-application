from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_404_NOT_FOUND,
	HTTP_200_OK,
	HTTP_201_CREATED
)
from django.shortcuts import get_object_or_404
from utils.api_response import APIFailure, APISuccess
from accounts.models import Account
from celery import shared_task
from services.paystack_service import PaystackService
from users.models import CustomUser
from utils.choices import Transaction
# Create your views here.


class ListCreateBeneficiariesView(generics.ListCreateAPIView):
	"""
	GET beneficiaries/
	POST beneficiaries/
	"""
	queryset = Beneficiary.objects.all()
	serializer_class = BeneficiarySerializer

	def get(self, request, *args, **kwargs):
		beneficiary = Beneficiary.objects.filter(user=request.user).first()
		if beneficiary:
			serializer = BeneficiarySerializer(beneficiary)
			return APISuccess(data=serializer.data)
		return APISuccess()
	
	def post(self, request, *args, **kwargs):
		beneficiary = BeneficiarySerializer(data=request.data)
		if beneficiary.is_valid():
			create_beneficiary.delay(request.user.id, request.data['uid'], request.data['uid2'])
			return APISuccess("Added Beneficiary succesfully")

		return APIFailure(beneficiary.errors, status=HTTP_400_BAD_REQUEST)

@shared_task
def create_beneficiary(user_id, account_no, bank_code):
	paystack = PaystackService()
	user = CustomUser.objects.get(id=user_id)
	response = paystack.create_transfer_recipient(user, account_no, bank_code)

	if response.get('status') == True:
		beneficiary, created = Beneficiary.objects.get_or_create(
			user = user,
			uid = response['data']['details']['account_number'],
			uid2 = response['data']['details']['bank_code'],
			recipient_code = response['data']['recipient_code'],
			recipient_name = response['data']['name'],
			is_default = True
		)
		user.default_withdraw_beneficiary = beneficiary
		user.save()
