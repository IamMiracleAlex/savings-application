from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404
from utils.api_response import APIFailure
from rest_framework.validators import UniqueValidator


class KYCProfileSerializer(serializers.ModelSerializer):
	bvn = serializers.CharField(
		required=True,
		validators=[UniqueValidator(queryset=KYCProfile.objects.all(), message='User with this BVN already exists')]
		)
	dob = serializers.CharField(required=True)
	verification_level = serializers.CharField(required=False, source='get_verification_level_display') 

	class Meta:
		model = KYCProfile
		fields = ('id', 'bvn', 'dob', 'verification_level', 'name', 'phone_number', 'created_at', 'updated_at')
