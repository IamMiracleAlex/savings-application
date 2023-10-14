import json

from django.contrib import admin
from django.db.models.functions import TruncDay
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum

from .models import Transaction, TransactionMetric
from utils.choices import Transaction as TransactionOptions



class TransactionAdmin(admin.ModelAdmin):
    model = Transaction
    list_display = ('account', 'type_of_account', 'type_of_transaction', 'amount', 'fee', 'total', 'status', 'reference', 'balance_after_transaction',  'memo', 'dest_account', 'data', 'created_at', 'updated_at',)
    list_filter = ('type_of_transaction', 'status')
    search_fields = ('reference', 'type_of_transaction', 'account__user__email','account__user__first_name', 'dest_account__user__email','dest_account__user__first_name',)
    ordering = ('-created_at',)
    actions = ['export_selected_to_csv']

    def type_of_account(self, obj):
        return obj.account.get_type_of_account_display()


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

admin.site.register(Transaction, TransactionAdmin)





@admin.register(TransactionMetric)
class TransactionMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/transactionmetric_change_list.html'
    transactions = TransactionMetric.objects.filter(status=TransactionOptions.SUCCESS)

    def changelist_view(self, request, extra_context=None):
        withdraw_chart_data = (
            self.transactions.filter(type_of_transaction=TransactionOptions.Withdraw).annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(y=Sum("amount"))
            .order_by("-date")
        )
        transfer_chart_data = (
            self.transactions.filter(type_of_transaction=TransactionOptions.Transfer).annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(y=Sum("amount"))
            .order_by("-date")
        )
        payment_chart_data = (
            self.transactions.filter(type_of_transaction=TransactionOptions.Payment).annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(y=Sum("amount"))
            .order_by("-date")
        )
        deposit_chart_data = (
            self.transactions.filter(type_of_transaction=TransactionOptions.Deposit).annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(y=Sum("amount"))
            .order_by("-date")
        )

        # Serialize and attach the chart data to the template context
        withdraw_as_json = json.dumps(list(withdraw_chart_data)[:50], cls=DjangoJSONEncoder)
        transfer_as_json = json.dumps(list(transfer_chart_data)[:50], cls=DjangoJSONEncoder)
        payment_as_json = json.dumps(list(payment_chart_data)[:50], cls=DjangoJSONEncoder)
        deposit_as_json = json.dumps(list(deposit_chart_data)[:50], cls=DjangoJSONEncoder)

        extra_context = extra_context or {
            "withdraw_as_json": withdraw_as_json,
            'transfer_as_json': transfer_as_json, 
            'payment_as_json': payment_as_json,
            'deposit_as_json': deposit_as_json,
            }

        return super().changelist_view(request, extra_context=extra_context,)

 