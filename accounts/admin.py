from django.contrib import admin
from .models import *

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    model = Account
    list_display = ('get_email', 'get_phone_number', 'public_id', 'type_of_account', 'balance', 'interest', 'interest_for_today', 'interest_active', 'created_at', 'updated_at',)
    list_filter = ('type_of_account',)
    search_fields = ('public_id', 'type_of_account', 'user__email', 'user__first_name')
    ordering = ('-updated_at',)

    def get_email(self, obj):
        return "{}'s {} account".format(obj.user.email, obj.get_type_of_account_display().title())
    get_email.short_description = "User's email"

    def get_phone_number(self, obj):
        return obj.user.phone_number
    get_phone_number.short_description = "User's phone_number"

admin.site.register(Account, AccountAdmin)