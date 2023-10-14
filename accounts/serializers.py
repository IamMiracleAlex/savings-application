from rest_framework import serializers
from .models import *


class AccountSerializer(serializers.ModelSerializer):
    type_of_account = serializers.CharField(source='get_type_of_account_display')
    class Meta:
        model = Account
        fields = ('id', 'type_of_account', 'balance', 'interest', 'interest_active', 'created_at', 'updated_at',)