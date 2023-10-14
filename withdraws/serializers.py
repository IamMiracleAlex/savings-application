from rest_framework import serializers
from .models import Withdraw, Beneficiary
from accounts.models import Account
from django.shortcuts import get_object_or_404



class BeneficiarySerializer(serializers.ModelSerializer):
	uid = serializers.CharField(required=True)
	uid2 = serializers.CharField(required=True)

	class Meta:
		model = Beneficiary
		fields = ('id', 'uid', 'uid2', 'recipient_code', 'recipient_name', 'is_default', 'created_at', 'updated_at')
