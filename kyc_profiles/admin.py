from django.contrib import admin
from .models import *
# Register your models here.
class KYCProfileAdmin(admin.ModelAdmin):
    model = KYCProfile
    list_display = ('user', 'bvn', 'name', 'phone_number', 'dob', 'verification_level', 'created_at', 'updated_at',)
    list_filter = ('verification_level',)
    search_fields = ('user__email', 'bvn', 'name', 'phone_number')
    ordering = ('-created_at',)

admin.site.register(KYCProfile, KYCProfileAdmin)