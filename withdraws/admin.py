from django.contrib import admin
from .models import *

# Register your models here.


class WithdrawAdmin(admin.ModelAdmin):
    model = Withdraw
    list_display = ('account', 'status', 'reference', 'amount', 'fee', 'beneficiary', 'created_at', 'updated_at',)
    list_filter = ('status',)
    search_fields = ('reference', 'account__user__email')
    ordering = ('-created_at',)

class BeneficiaryAdmin(admin.ModelAdmin):
    model = Beneficiary
    list_display = ('user', 'uid', 'uid2', 'recipient_name', 'is_default', 'created_at', 'updated_at',)
    search_fields = ('user__phone_number', 'recipient_name')
    ordering = ('-created_at',)

# admin.site.register(Withdraw, WithdrawAdmin)
admin.site.register(Beneficiary, BeneficiaryAdmin)