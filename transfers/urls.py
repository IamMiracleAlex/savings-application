from django.urls import path
from django.conf.urls import url

from . import views

app_name = "transfer"
urlpatterns = [
    # path("", views.ListCreateTransfersView.as_view(), name="transfer"),
    path("recipient", views.GetTransferRecipientView.as_view(), name="transfer_recipient"),
]
