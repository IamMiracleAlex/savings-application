from django.contrib import admin
from .models import *




class FundSourceAdmin(admin.ModelAdmin):
    model = FundSource
    list_display = ('user', 'last4', 'bank_name', 'card_type', 'exp_month', 'exp_year', 'is_active', 'created_at', 'updated_at',)
    list_filter = ('is_active',)
    search_fields = ('user__phone_number', 'user__email', 'last4', 'card_type', 'bank_name')
    ordering = ('-created_at',)


# admin.site.register(Deposit, DepositAdmin)
admin.site.register(FundSource, FundSourceAdmin)