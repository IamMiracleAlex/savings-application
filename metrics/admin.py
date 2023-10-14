from datetime import datetime
import csv

from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponseRedirect, HttpResponse

from .models import Metric
from .views import calculate_metrics



# Register your models here.
class MetricAdmin(admin.ModelAdmin):
    model = Metric
    change_list_template = 'admin/metrics_changelist.html'

    list_display = ('start_date','end_date','new_users','activated_users_count','total_deposits','total_deposits_volume','total_withdraws',
        'total_withdraws_volume','total_transfers','total_transfers_volume','total_payments','total_payments_volume', 'bill_payment_fees_volume', 'autosave_breaking_fees_volume',
        'wallet_balance', 'autosave_balance','target_balance', 'total_interests_for_today', 'total_interests_volume','created_at','updated_at')
    search_fields = ('start_date', 'end_date')
    ordering = ('-created_at',)
    date_hierarchy = 'start_date'
    list_filter = ('start_date','created_at')

    actions = ['export_selected_to_csv']


    def export_selected_to_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    def get_urls(self):
        
        urls = super().get_urls()
        my_urls = [
            path('custom-metric/', self.admin_site.admin_view(self.custom_metric), name='custom_metric')
        ]
        return my_urls + urls


    def custom_metric(self, request, *args, **kwargs):
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        processed_start_date = None
        processed_end_date = None

        if start_date and end_date:    
            try:
                processed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
                processed_end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except:
                self.message_user(request, f'ERROR, incorrect date format. Please use Google chrome browser.')
                return HttpResponseRedirect(reverse("admin:metrics_metric_changelist"))


        calculate_metrics(start_date=processed_start_date, end_date=processed_end_date)

        self.message_user(request, f'Success, metric from "{processed_start_date}" to "{processed_end_date}" has been generated.')
       
        return HttpResponseRedirect(reverse("admin:metrics_metric_changelist"))        



admin.site.register(Metric, MetricAdmin)