from django.urls import path, include
from django.conf.urls import url

from . import views

app_name = "web"
urlpatterns = [
    path("", views.index, name="index"),
    path("terms_and_conditions/", views.terms, name="terms"),
    path("register/", views.register, name="register"),
    path("s/<str:refer_code>", views.referral_signup, name="referral_signup"),
    path("faq/", views.faq, name="faq"),
    path("about/", views.about, name="about"),
]
