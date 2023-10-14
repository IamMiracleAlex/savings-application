from django.urls import path, include
from django.conf.urls import url

from . import views

app_name = "users"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.SignUpView.as_view(), name="register"),
    path("users/me/", views.UsersDetailsView.as_view(), name="users"),
    path("users/me/enable_notifications/", views.EnableNotifications.as_view(), name="enable_notifications"),
    path("users/me/disable_notifications/", views.DisableNotifications.as_view(), name="disable_notifications"),
    path("users/me/send_email_activation/", views.SendActivationEmail.as_view(), name="send_activation_email"),
    path("users/activate/<str:uidb64>/<str:token>", views.ActivateEmail.as_view(), name="activate_email"),
    path("users/test_email/", views.test_email, name="test_email"),
    
]
