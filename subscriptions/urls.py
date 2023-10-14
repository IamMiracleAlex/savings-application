from django.urls import path
from django.conf.urls import url

from . import views

app_name = "subscriptions"
urlpatterns = [
    path("subscription", views.RetrieveUpdateSubscriptionView.as_view(), name="subscription"),    
    path("subscription/enable", views.EnableSubscription.as_view(), name="enable_subscription"),    
    path("subscription/disable", views.DisableSubscription.as_view(), name="disable_subscription"),    
    path("subscriptions", views.CreateSubscriptionsView.as_view(), name="subscriptions"),    
]