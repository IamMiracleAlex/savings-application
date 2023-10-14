from django.urls import path
from django.conf.urls import url

from . import views

app_name = "transactions"
urlpatterns = [
    path("", views.ListCreateTransactionsView.as_view(), name="transactions"),    
]