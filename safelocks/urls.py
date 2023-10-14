from django.urls import path
from django.conf.urls import url

from . import views

app_name = "safelocks"
urlpatterns = [
    path("safelocks/", views.ListCreateSafeLocksView.as_view(), name="safelocks"),    
    path("safelock/", views.RetrieveUpdateSafeLockView.as_view(), name="safelock"),    
]