from django.urls import path
from django.conf.urls import url

from . import views

app_name = "accounts"
urlpatterns = [
    path("", views.ListAccountsView.as_view(), name="accounts"),
    path("<str:type_of_account>", views.GetAccountView.as_view(), name="account"),
]