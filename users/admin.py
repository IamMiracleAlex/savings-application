import json
import csv

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models.functions import TruncDay
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.urls import path, reverse
from django.utils.html import format_html

from .models import CustomUser, UserMetric, MassNotification
from services.firebase_service import send_notification
from accounts.models import Account
from transactions.models import Transaction
from safelocks.models import SafeLock
from subscriptions.models import Subscription
from deposits.models.fund_source import FundSource
from withdraws.models.beneficiary import Beneficiary
from kyc_profiles.models import KYCProfile
from django.db.models import Q


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    change_form_template = 'admin/users_change_form.html'

    list_display = ('public_id', 'first_name', 'last_name', 'email', 'phone_number', 'refered_by', 'kyc_level', 'no_of_referrals', 'no_of_activated_referrals', 'is_staff', 'email_verified',  'account_activated',  'is_active', 'account_number',  'created_at', 'updated_at',)
    list_filter = ('is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'default_deposit_fund_source', 'default_withdraw_beneficiary', 'account_activated', 'email_verified', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active','groups')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email','phone_number','first_name','last_name')
    ordering = ('-created_at',)
    actions = ['export_as_csv']


    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        accounts = Account.objects.filter(user__id=object_id)
        transactions = Transaction.objects.filter(Q(account__in=accounts) | Q(dest_account__in=accounts)).order_by('-id')[:10]
        safelocks = SafeLock.objects.filter(account__in=accounts)
        subscriptions = Subscription.objects.filter(account__in=accounts)
        fundsources = FundSource.objects.filter(user__id=object_id)
        kycprofiles = KYCProfile.objects.filter(user__id=object_id)
        beneficiaries = Beneficiary.objects.filter(user__id=object_id)
        referrals = CustomUser.objects.filter(referer__id=object_id, account_activated=True)

        extra_context['accounts'] = accounts
        extra_context['transactions'] = transactions
        extra_context['safelocks'] = safelocks
        extra_context['subscriptions'] = subscriptions
        extra_context['fundsources'] = fundsources
        extra_context['beneficiaries'] = beneficiaries
        extra_context['kycprofiles'] = kycprofiles
        extra_context['referrals'] = referrals

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    
    def no_of_referrals(self, obj):
        return obj.referrals.all().count()

    def no_of_activated_referrals(self, obj):
        return obj.referrals.filter(account_activated=True).count()

    def refered_by(self, obj):
        if obj.referer:
            return obj.referer.full_name()
        return None

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export to CSV"
admin.site.register(CustomUser, CustomUserAdmin)



@admin.register(UserMetric)
class UserMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/usermetric_change_list.html'

    def changelist_view(self, request, extra_context=None):
        # Aggregate new users per day
        chart_data = (
            UserMetric.objects.annotate(date=TruncDay("date_joined"))
            .values("date")
            .annotate(y=Count("id"))
            .order_by("-date")
        )

        # Serialize and attach the chart data to the template context
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        extra_context = extra_context or {"chart_data": as_json}

        response = super().changelist_view(
            request, extra_context=extra_context,)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        
        # Count of all users
        metrics = {
            'total': Count('id'),
        }
    
        response.context_data['summary_total'] = dict(
            qs.aggregate(**metrics)
        )

        return response

    def get_urls(self):
        # Url for async data reload
        urls = super().get_urls()
        custom_urls = [
            path("chart_data/", self.admin_site.admin_view(self.chart_data_endpoint))
        ]
        return custom_urls + urls


    def chart_data_endpoint(self, request):
        # returns data as json
        chart_data = self.chart_data()
        return JsonResponse(list(chart_data), safe=False)

    def chart_data(self):
        # helper function for aggregating users
        return (
            UserMetric.objects.annotate(date=TruncDay("date_joined"))
            .values("date")
            .annotate(y=Count("id"))
            .order_by("-date")
        )



class MassNotificationAdmin(admin.ModelAdmin):
    model = MassNotification

    list_display = ('title','created_at','author','modified_by','updated_at','notify_users','notify_admins')
    search_fields = ['title',]
    list_filter = ['created_at', 'updated_at']
    exclude = ['author','modified_by']


    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:notify_id>/notify-users/', self.admin_site.admin_view(self.user_notifications), {'is_staff':False}, name='user_notifications'),
            path('<int:notify_id>/notify-users/is_staff', self.admin_site.admin_view(self.user_notifications), {'is_staff':True}, name='admin_notifications'),
        ]
        return my_urls + urls

    def notify_users(self, obj):
        return format_html(
            '<a class="button" href="{}">Notify Users</a>',
            reverse('admin:user_notifications', args=[obj.id])
        )

    def notify_admins(self, obj):
        return format_html(
            '<a class="button" href="{}">Notify Admins</a>',
            reverse('admin:admin_notifications', args=[obj.id])
        )    
    
    notify_users.short_description = 'Notify all Users'
    notify_admins.short_description = 'Notify all Admins'



    def user_notifications(self, request, notify_id, is_staff, *args, **kwargs):
        if (is_staff == True):
            user_ids = [ p.id for p in CustomUser.objects.filter(is_staff=True) ]
            user_type = 'admin'
        else:
            user_ids = [ p.id for p in CustomUser.objects.all() ] 
            user_type = ''
        obj = self.get_object(request, notify_id) 

        self.handle_notifications(
            request=request,
            obj=obj,
            user_ids=user_ids
        )
        self.message_user(request, f'Success, "{obj.title}" has been sent to all {user_type} users.')
        return HttpResponseRedirect(reverse("admin:users_massnotification_changelist"))

   
    def handle_notifications(self, request, obj, user_ids):

        for user_id in user_ids:
            send_notification.delay(user_id, obj.title, obj.message)

    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)    


admin.site.register(MassNotification, MassNotificationAdmin)

