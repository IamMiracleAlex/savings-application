from django.contrib import admin
from .models import *

# Register your models here.
class SafeLockAdmin(admin.ModelAdmin):
    model = SafeLock
    list_display = ('account', 'name', 'get_account_balance',  'amount', 'interest', 'is_active', 'maturity_date', 'created_at', 'updated_at',)
    search_fields = ('name',)
    ordering = ('-created_at',)
    def get_account_balance(self, obj):
        return obj.account.balance
    get_account_balance.short_description = 'Account Balance'
    get_account_balance.admin_order_field = 'account__balance'


admin.site.register(SafeLock, SafeLockAdmin)