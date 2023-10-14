from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.serializers import AccountSerializer
from accounts.models import Account
from transfers.models import Transfer
from transfers.serializers import TransferSerializer
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionSerializer
from safelocks.models import SafeLock
from safelocks.serializers import SafeLockSerializer
from deposits.serializers import FundSourceSerializer
from deposits.models import FundSource, Deposit
from withdraws.models import Beneficiary, Withdraw
from withdraws.serializers import BeneficiarySerializer
from kyc_profiles.serializers import KYCProfileSerializer
from utils.choices import Transaction as TransactionOptions
from transactions.serializers import TransactionSerializer
from transactions.models import Transaction
from .models import *
from django.db.models import Q


class UserSerializer(serializers.ModelSerializer):
    accounts = serializers.SerializerMethodField(read_only=True)
    referrals = serializers.SerializerMethodField(read_only=True)
    fund_sources = serializers.SerializerMethodField(read_only=True)
    transactions = serializers.SerializerMethodField(read_only=True)
    subscription = serializers.SerializerMethodField(read_only=True)
    safelocks = serializers.SerializerMethodField(read_only=True)
    default_deposit_fund_source = serializers.SerializerMethodField(read_only=True)
    default_withdraw_beneficiary = serializers.SerializerMethodField(read_only=True)
    kyc_profile = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(
            required=False,
            validators=[UniqueValidator(queryset=CustomUser.objects.all(), message='User with this email already exists')]
            )
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    refer_code = serializers.CharField(required=False, read_only=True)
    phone_number = serializers.CharField(min_length=8, required=True, validators=[UniqueValidator(queryset=CustomUser.objects.all(), message='User with this phone number already exists')])

    
    def get_fund_sources(self, obj):
        fund_sources = FundSource.objects.filter(user=obj, is_active=True)
        return FundSourceSerializer(fund_sources, many=True).data

    def get_transactions(self, obj):
        accounts = Account.objects.filter(user=obj)
        transactions = Transaction.objects.filter(Q(account__in=accounts) | Q(dest_account__in=accounts) ).order_by('-id')[:50]
        return TransactionSerializer(transactions, many=True).data

    def get_subscription(self, obj):
        account = Account.objects.get(user=obj, type_of_account=Account.DIRECT)
        subscription = Subscription.objects.filter(account=account).last()
        if  subscription:
            return SubscriptionSerializer(subscription).data
        return {}

    def get_safelocks(self, obj):
        account = Account.objects.get(user = obj, type_of_account = Account.DEPOSIT)
        safelocks = SafeLock.objects.filter(account=account, is_active=True).order_by('-id')[:10]
        return SafeLockSerializer(safelocks, many=True).data

    def get_accounts(self, obj):
        ac_s = Account.objects.filter(user=obj)
        accounts = AccountSerializer(ac_s, many=True).data
        return { i['type_of_account']: i for i in accounts }

    def get_referrals(self, obj):
        referrals = CustomUser.objects.filter(referer=obj).order_by('-id')
        referrals = UserSerializer(referrals, many=True).data
        return [ 
            {'Name': i['full_name'], 
            'Phone Number': i['phone_number'], 
            'Email Verified': i['email_verified'],
            'Email': i['email'],
            'Account Activated': i['account_activated'],
            'Created At': i['created_at']
        } for i in referrals]
    
    def get_kyc_profile(self, obj):
        kyc = KYCProfile.objects.get(user=obj)
        return KYCProfileSerializer(kyc).data

    def get_default_deposit_fund_source(self, obj):
        fs = obj.default_deposit_fund_source
        if fs:
            fund_source = FundSource.objects.filter(id=fs.id).first()
            fund_source = FundSourceSerializer(fs).data
            return fund_source
        return None
    
    def get_default_withdraw_beneficiary(self, obj):
        bn = obj.default_withdraw_beneficiary
        if bn:
            beneficiary = Beneficiary.objects.filter(id=bn.id).first()
            beneficiary = BeneficiarySerializer(bn).data
            return beneficiary
        return None

    def create(self, validated_data):
        user = CustomUser.objects.create(
            phone_number=validated_data['phone_number']
        )
        user.set_password(validated_data['password'])
        if self.initial_data.get('refer_code'):
            referer = CustomUser.objects.filter(refer_code=self.initial_data['refer_code'].lower()).first()
            if referer:
                user.referer = referer
        if self.initial_data.get('first_name'):
            user.first_name = self.initial_data.get('first_name')
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email).lower()
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

    class Meta:
        model = CustomUser
        fields = (
            'public_id', 'email', 'phone_number', 'password', 'first_name', 'last_name', 'full_name', 'is_staff', 'refer_code', 'account_number', 'account_bank_name', 
            'email_verified', 'account_activated', 'send_notifications', 'kyc_profile', 'accounts', 'transactions', 'fund_sources',
            'subscription', 'safelocks', 'default_deposit_fund_source', 'default_withdraw_beneficiary',  'referrals', 'created_at', 'updated_at',)