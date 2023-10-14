from rest_framework import generics
from rest_framework.response import Response
from .models import Transfer
from accounts.models import Account
from .serializers import TransferSerializer
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_201_CREATED
)
from django.shortcuts import get_object_or_404
from utils.api_response import APIFailure, APISuccess
from users.serializers import  UserSerializer
from users.models import CustomUser
from utils.choices import Transaction

class ListCreateTransfersView(generics.ListCreateAPIView):
    """
    GET transfers/
    POST transfers/
    """
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer

    def get(self, request, type_of_account, *args, **kwargs):
        type_of_account = getattr(Account, type_of_account.upper(), 10)
        account = get_object_or_404(Account, user=request.user, type_of_account=type_of_account)

        transfers_out = Transfer.objects.filter(from_account=account, status=Transaction.SUCCESS).order_by('-id')
        transfers_in = Transfer.objects.filter(to_account=account, status=Transaction.SUCCESS).order_by('-id')
        outbound = TransferSerializer(transfers_out, many=True).data
        inbound = TransferSerializer(transfers_in, many=True).data
        return APISuccess(data={
            'inbound': inbound,
            'outbound': outbound
            })
    
    def post(self, request, type_of_account, *args, **kwargs):
        transfer = TransferSerializer(data=request.data, context=self.get_renderer_context())
        if transfer.is_valid():
            transfer = transfer.save()
            transfer.succeed()
            return APISuccess(data=TransferSerializer(transfer).data, status=HTTP_200_OK)

        return APIFailure(transfer.errors, status=HTTP_400_BAD_REQUEST)

class GetTransferRecipientView(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        phone_number = request.GET.get('phone_number')
        if phone_number:
            user = CustomUser.objects.filter(phone_number=phone_number).first()
            if user:
                data = {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'to_account_id': user.account_set.all().get(type_of_account=Account.WALLET).id
                }
                return APISuccess(data=data)
            else:
                return APIFailure(
                    message = "User with phone number: {} does not exist".format(phone_number), 
                    status=HTTP_404_NOT_FOUND
                )
        return APIFailure(
            message = "Please send a phone number", 
            status=HTTP_400_BAD_REQUEST
        )

