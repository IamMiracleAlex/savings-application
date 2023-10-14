from rest_framework import serializers
from accounts.models import Account
from .models import *
from django.shortcuts import get_object_or_404
from utils.api_response import APIFailure
from transactions.models import TransactionOptions



class AddCardSerializer(serializers.Serializer):
	reference = serializers.CharField(required=True)
	amount = serializers.IntegerField(required=True)



class FundSourceSerializer(serializers.ModelSerializer):
	class Meta:
		model = FundSource
		fields = ('id', 'last4', 'bank_name', 'card_type', 'exp_month', 'exp_year', 'is_active', 'created_at', 'updated_at')
