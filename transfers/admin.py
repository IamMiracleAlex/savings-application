from django.contrib import admin
from .models import *
# Register your models here.


class TransferAdmin(admin.ModelAdmin):
    model = Transfer
    list_display = ('get_transfer_type', 'status', 'reference', 'amount', 'fee', 'created_at', 'updated_at',)
    list_filter = ('status',)
    search_fields = ('reference', 'from_account__user__email', 'to_account__user__email')
    ordering = ('-created_at',)

# admin.site.register(Transfer, TransferAdmin)