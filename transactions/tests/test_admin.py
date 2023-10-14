from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.urls import reverse

from users.models import CustomUser
from accounts.models import Account
from transactions.models import Transaction, TransactionMetric
from utils.choices import Transaction as TransactionOptions
from transactions import admin



class TransactionAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(phone_number='2348026043569', 
                            password='password123', email='example@gmail.com',
                            first_name='Miracle', last_name='Alex')
        cls.account = Account.objects.filter(user=cls.user).first()

        '''Instantiate admin site'''
        
        cls.site = AdminSite() # configure admin for testing

        cls.trans_admin = admin.TransactionAdmin(Transaction, cls.site)

    def test_type_of_account(self):
        '''test type_of_account() method'''

        # sample trans data

        trans_data = {'account':self.account,
                'type_of_transaction':TransactionOptions.Withdraw,
                'status':TransactionOptions.SUBMITTED,
                'reference': 'qwerty',
                'amount': 200,
                'balance_after_transaction': 200,
                'fee': 100,
                'memo': 'deposit',
                }
        trans = Transaction.objects.create(**trans_data)

        # method returns correct type of account

        result = self.trans_admin.type_of_account(trans)
        self.assertEqual(result, self.account.get_type_of_account_display())



class TransactionMetricAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.site = AdminSite()
        cls.trans_admin = admin.TransactionMetricAdmin(TransactionMetric, cls.site)

        # instantiate request obj

        cls.request = HttpRequest()

        CustomUser.objects.create_superuser(phone_number='08026043569', email='email@example.com', password='password123')


    def test_change_list_view(self):
        '''Test that chart data page loads'''

        self.client.login(phone_number='08026043569',password='password123')

        # use dynamic url
        page = self.client.get(reverse('admin:transactions_transactionmetric_changelist'))

        # page loads up, and with expected template

        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed('transactionmetric_change_list.html')
        self.client.logout()