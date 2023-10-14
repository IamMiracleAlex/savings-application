from django.shortcuts import render
from rest_framework import generics
from services.paystack_service import PaystackService
from .models import KYCProfile
from .serializers import *
from utils.api_response import APISuccess, APIFailure
# Create your views here.

class VerifyBVN(generics.CreateAPIView):
	serializer_class = KYCProfileSerializer

	def post(self, request, *args, **kwargs):
		data = KYCProfileSerializer(
			data=request.data,
			context=self.get_renderer_context()
		)
		kyc_profile = KYCProfile.objects.get(user=request.user)

		if data.is_valid():
			paystack = PaystackService()
			resp = paystack.verify_bvn(request.data['bvn'])
			if (resp['status'] == True):
				resp = resp['data']
				kyc_profile.name = "{} {}".format(resp['first_name'], resp['last_name'])
				kyc_profile.bvn = resp['bvn']
				kyc_profile.dob = resp['dob']
				kyc_profile.phone_number = resp['mobile']
				kyc_profile.verification_level = KYCProfile.LEVEL_1
				kyc_profile.save()
				return APISuccess(message = 'BVN verified successfully', data=KYCProfileSerializer(kyc_profile).data)  
			else:
				return APIFailure(message='Unable to verify BVN')  
		return APIFailure(message=data.errors)  