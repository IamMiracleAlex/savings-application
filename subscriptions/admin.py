from django.contrib import admin
from .models import *

# Register your models here.

from django.contrib import admin
from .models import *

# Register your models here.
class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = ('account', 'name', 'amount', 'interval', 'is_active', 'start_date', 'previous_paydate', 'next_paydate', 'created_at', 'updated_at',)
    search_fields = ('name',)
    ordering = ('-created_at',)


admin.site.register(Subscription, SubscriptionAdmin)