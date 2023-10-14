from rest_framework import serializers
from accounts.models import Account
from .models import *
from django.shortcuts import get_object_or_404
from utils.api_response import APIFailure
from accounts.serializers import AccountSerializer
from datetime import date
from decimal import Decimal

class TransferSerializer(serializers.ModelSerializer):
	WITHDRAWAL_DATES = ["2020-03-28", "2020-06-28", "2020-09-28", "2020-12-28"]
	amount = serializers.IntegerField(required=True)
	from_account = serializers.SerializerMethodField(read_only=True)
	to_account_id = serializers.IntegerField(required=True, write_only=True)
	to_account = serializers.SerializerMethodField(read_only=True)
	reference = serializers.CharField(required=True)
	status = serializers.CharField(source='get_status_display', read_only=True)
	transfer_type = serializers.CharField(source='get_transfer_type', read_only=True)
	type_of_transaction = serializers.SerializerMethodField(read_only=True)
	
	def validate(self, data):
		type_of_account = getattr(
			Account, 
			self.context['view'].kwargs['type_of_account'].upper(), 
			10
		)
		from_account = get_object_or_404(Account, user=self.context['request'].user, type_of_account=type_of_account)
		data['from_account'] = from_account
		to_account = get_to_account(from_account, data['to_account_id'])
		data['to_account'] = to_account

		if (from_account.type_of_account == Account.DIRECT):
			today = date.today().strftime('%Y-%m-%d')
			if today not in self.WITHDRAWAL_DATES:
				data['fee'] = Decimal(data['amount'] * 0.05)
		else:
			data['fee'] = Decimal(0)
		if (from_account.type_of_account == Account.WALLET and to_account.type_of_account == Account.WALLET):
			data['transfer_type'] = Transfer.PeerToPeer
		else:
			data['transfer_type'] = Transfer.InternalTransfer
		if from_account == to_account:
			raise serializers.ValidationError("Invalid transaction")
		if ((data['amount'] + data['fee']) > from_account.balance):
			raise serializers.ValidationError("Insufficient Balance")
		if (to_account.type_of_account == Account.DEPOSIT) or not to_account:
			raise serializers.ValidationError("Destination Account not valid")
		return data

	def create(self, validated_data):
		transfer_obj, new_obj = Transfer.objects.get_or_create(
			from_account = validated_data['from_account'],
			to_account = validated_data['to_account'],
			amount = validated_data['amount'],
			reference = validated_data['reference'],
			fee = validated_data['fee'],
			transfer_type = validated_data['transfer_type']
		)
		# This line ensures that the transfer being succeeded is a newly created transfer and not an existing one
		if new_obj:
			transfer_obj.succeed()
		return transfer_obj

	def get_type_of_transaction(self, obj):
		return "Transfer"

	def get_from_account(self, obj):
		ac = Account.objects.get(id=obj.from_account.id)
		account = AccountSerializer(ac).data
		return account

	def get_to_account(self, obj):
		ac = Account.objects.get(id=obj.to_account.id)
		account = AccountSerializer(ac).data
		return account

	class Meta:
		model = Transfer
		fields = ('id', 'amount', 'fee', 'status', 'transfer_type', 'transaction_description', 'type_of_transaction', 'reference', 'from_account', 'to_account_id', 'to_account', 'created_at', 'updated_at')


def get_to_account(from_account, to_account_id):
	if (from_account.type_of_account == Account.DEPOSIT) or (from_account.type_of_account == Account.DIRECT):
		return Account.objects.get(type_of_account=Account.WALLET, user=from_account.user)
	return Account.objects.get(id=to_account_id)