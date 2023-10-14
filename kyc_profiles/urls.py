from django.urls import path
from django.conf.urls import url

from . import views

app_name = "kyc_profiles"
urlpatterns = [
    path("", views.VerifyBVN.as_view(), name="kyc_profiles"),    
]