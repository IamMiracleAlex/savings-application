"""savest_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
import deposits.views
import withdraws.views
import kyc_profiles.views
import safelocks.views
import transactions.webhooks
import transactions.views


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('web.urls')),
    path('api/v1/', include('users.urls')),
    path('api/v1/users/me/accounts/', include('accounts.urls')),
    path('api/v1/users/me/accounts/<str:type_of_account>/transactions/', include('transactions.urls')),
    path('api/v1/users/me/accounts/<str:type_of_account>/deposits/', include('deposits.urls')),
    path('api/v1/users/me/withdrawals/', include('withdraws.urls')),
    path('api/v1/users/me/payments/', include('payments.urls')),
    path('api/v1/users/me/bvn_verification/', include('kyc_profiles.urls')),
    path('api/v1/users/me/accounts/<str:type_of_account>/transfers/', include('transfers.urls')),
    path('api/v1/users/me/accounts/<str:type_of_account>/', include('subscriptions.urls')),
    path("webhooks/paystack", deposits.views.PaystackWebhook.as_view(), name='paystack'),
    path("webhooks/paystackk", transactions.webhooks.PaystackWebhook.as_view(), name='paystackk'),
    path("webhooks/monnify", deposits.views.MonnifyWebhook.as_view(), name='monnify'),
    path("webhooks/monnifyy", transactions.webhooks.MonnifyWebhook.as_view(), name='monnifyy'),
    path("paystack/add_card", deposits.views.PaystackAddCard.as_view(), name='paystack_addcard'),
    path("api/v1/users/me/fund_sources/", deposits.views.RetrieveFundSourceView.as_view(), name="fund_sources"),
    path("api/v1/users/me/fund_sources/set_default/", deposits.views.ChangeDefaultFundSource.as_view(), name="default_fund_source"),
    path("api/v1/users/me/beneficiary/", withdraws.views.ListCreateBeneficiariesView.as_view(), name="beneficiaries"),
    path("api/v1/users/me/", include('safelocks.urls')),
    path("accounts/", include('rest_auth.urls')),
    path("accounts/", include('django.contrib.auth.urls')),
    path('paystack/initialize/', transactions.views.InitializeTransaction.as_view(), name="paystack_initialize"),    
    path('paystack/resolve-account-bank/', transactions.views.ResolveAccountNumber.as_view(), name="paystack_resolve_acct_number"),    
    path('api/v1/chicken-change-deposit/', transactions.views.ChickenChangeView.as_view(), name="chicken_change_deposit"),    


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)