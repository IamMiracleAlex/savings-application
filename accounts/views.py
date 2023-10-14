from django.shortcuts import render
from .models import *
from .serializers import AccountSerializer
from rest_framework import generics
from utils.api_response import APISuccess, APIFailure
from django.shortcuts import get_object_or_404
from utils.helpers import generate_random_number
from transfers.models import Transfer
from datetime import date, timedelta
from django.utils import timezone


class ListAccountsView(generics.ListAPIView):
    """
    GET accounts/
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    
    def get(self, request, *args, **kwargs):
        accounts = Account.objects.filter(user=request.user)
        accounts = AccountSerializer(accounts, many=True)
        accounts = { i['type_of_account']: i for i in accounts.data }
        return APISuccess( data = accounts )

class GetAccountView(generics.RetrieveAPIView):
    """
    GET accounts/
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    
    def get(self, request, type_of_account, *args, **kwargs):
        type_of_account = getattr(Account, type_of_account.upper(), 10)
        account = get_object_or_404(Account, user=request.user, type_of_account=type_of_account)
        return APISuccess( data = AccountSerializer(account).data )
