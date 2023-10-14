from rest_framework import generics
from rest_framework.response import Response
from services.paystack_service import PaystackService
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from accounts.models import Account
from utils.api_response import APIFailure, APISuccess
from .models import *
from .serializers import *
from utils.helpers import generate_unique_id
from celery import shared_task
from transfers.models import Transfer
from transactions.models import Transaction, TransactionOptions
from deposits.models import FundSource
from deposits.views import create_referral_deposit


class ListCreateSafeLocksView(generics.ListCreateAPIView):
    """
	GET safelocks/
	POST safelocks/
	"""

    queryset = SafeLock.objects.all()
    serializer_class = SafeLockSerializer

    def get(self, request, *args, **kwargs):
        account = Account.objects.get(
            user=request.user, type_of_account=Account.DEPOSIT
        )
        safelocks = SafeLock.objects.filter(account=account, is_active=True).order_by(
            "-id"
        )
        serializer = SafeLockSerializer(safelocks, many=True)
        return APISuccess(data=serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = SafeLockSerializer(
            data=request.data, context=self.get_renderer_context()
        )
        if serializer.is_valid():
            safelock = serializer.save()
            if request.data["transfer_from"] == "wallet":
                if create_transfer(
                    safelock, request.data["reference"], safelock.amount
                ):
                    safelock.activate()
                    if not safelock.account.user.paid_referer_bonus:
                        user = safelock.account.user
                        create_referral_deposit(user)
                    return APISuccess(
                        data=SafeLockSerializer(safelock).data,
                        message="Term Deposit created successfully",
                    )
            else:
                message, deposit = activate_safelock_deposit(
                    safelock.id, request.data["reference"], safelock.amount
                )
                if (deposit.status == TransactionOptions.SUCCESS):
                    if not deposit.account.user.paid_referer_bonus:
                        user = deposit.account.user
                        create_referral_deposit(user)
                return APISuccess(
                    data=SafeLockSerializer(safelock).data, message=message
                )
        return APIFailure(message=serializer.errors, status=HTTP_400_BAD_REQUEST)


class RetrieveUpdateSafeLockView(generics.RetrieveUpdateAPIView):
    """
	PUT safelock/
	"""

    queryset = SafeLock.objects.all()
    serializer_class = SafeLockSerializer

    def put(self, request, *args, **kwargs):
        safelock = SafeLock.objects.get(id=request.data["id"])
        serializer = SafeLockSerializer(
            data=request.data, partial=True, context=self.get_renderer_context()
        )
        if serializer.is_valid():
            amount = serializer.validated_data["amount"]
            if request.data["transfer_from"] == "wallet":
                if create_transfer(safelock, request.data["reference"], amount):
                    safelock.amount += amount
                    safelock.save()
                    return APISuccess(
                        data=SafeLockSerializer(safelock).data,
                        message="Term Deposit updated successfully",
                    )
            else:
                message, deposit = activate_safelock_deposit(
                    safelock.id, request.data["reference"], amount
                )
                return APISuccess(
                    data=SafeLockSerializer(safelock).data, message=message
                )
        return APIFailure(message=serializer.errors, status=HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        account = Account.objects.get(
            user=request.user, type_of_account=Account.DEPOSIT
        )
        safelock = SafeLock.objects.filter(
            account=account, id=int(request.GET.get("id")), is_active=True
        ).first()
        serializer = SafeLockSerializer(safelock)
        return APISuccess(data=serializer.data)


def create_transfer(safelock, ref, amount):
    user = safelock.account.user
    from_account = Account.objects.get(user=user, type_of_account=Account.WALLET)
    to_account = Account.objects.get(user=user, type_of_account=Account.DEPOSIT)

    transaction = Transaction.objects.create(
        account=from_account,
        type_of_transaction=TransactionOptions.Transfer,
        amount=amount,
    )
    transaction.dest_account_id = to_account.id
    transaction.dest_account = to_account
    transaction.data = {}
    transaction.data["transfer_type"] = "InternalTransfer"
    transaction.save()
    transaction.process()
    return transaction.succeed()


@shared_task
def activate_safelock_deposit(safelock_id, ref, amount):
    safelock = SafeLock.objects.get(id=safelock_id)
    deposit = safelock.create_deposit(ref, amount)

    paystack = PaystackService()
    fund_source = FundSource.objects.get(id=deposit.data["fund_source_id"])
    response = paystack.charge_card(deposit, fund_source)
    if response["status"] == True:
        if response["data"]["status"] == "success":
            deposit.succeed()
            if safelock.is_active == True:
                safelock.amount += deposit.amount
            safelock.activate()
            return response['message'], deposit
    deposit.data['failure_reason'] = response.get('data')['gateway_response']
    response['message'] = deposit.data['failure_reason']
    deposit.reject()
    return response['message'], deposit
