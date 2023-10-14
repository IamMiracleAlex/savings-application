from django.shortcuts import render
from .models import Payment
from rest_framework import generics
from .serializers import PaymentSerializer
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_201_CREATED
)
from django.shortcuts import get_object_or_404
from utils.api_response import APIFailure, APISuccess
from services.ravepay_service import RavepayService
# Create your views here.

class ListCreatePaymentsView(generics.ListCreateAPIView):
	"""
	GET payments/
	POST payments/
	"""
	queryset = Payment.objects.all()
	serializer_class = PaymentSerializer

	def get(self, request, *args, **kwargs):
		payments = Payment.objects.filter(user=request.user).order_by('-id')
		serializer = PaymentSerializer(payments, many=True)
		return APISuccess(data=serializer.data)
	
	def post(self, request, *args, **kwargs):
		payment = PaymentSerializer(data=request.data, context=self.get_renderer_context())
		if payment.is_valid():
			payment = payment.save()
			payment.process()
			ravepay = RavepayService()
			response = ravepay.bill_payments(payment)
			if (response['data']['Status'] == 'success'):
				payment.succeed()
				return APISuccess(message="Bill payment was Successful", data=PaymentSerializer(payment).data, status=HTTP_200_OK)
			payment.reject()
			return APIFailure(message=response['data']['Message'], status=HTTP_400_BAD_REQUEST)

		return APIFailure(payment.errors, status=HTTP_400_BAD_REQUEST)