from django.contrib import admin
from .models import *

# Register your models here.


class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = ('user', 'status', 'reference', 'type_of_biller', 'name_of_biller', 'fund_source', 'fund_source_type', 'created_at', 'updated_at',)
    search_fields = ('reference', 'name_of_biller', 'user__email')
    ordering = ('-created_at',)


# admin.site.register(Payment, PaymentAdmin)