from django.test import SimpleTestCase
from django.urls import reverse, resolve

from transactions import views




class TransactionsUrlsPatternsTest(SimpleTestCase):
    
    def test_list_create_transactions_url(self):
        '''assert that the name returns the required path for list create 
        transactions url'''

        url_name = reverse('transactions:transactions', args=['type_of_account'])
        url_path = '/api/v1/users/me/accounts/type_of_account/transactions/'
        self.assertEqual(url_name, url_path)

    def test_initialize_transactions_url(self):
        '''assert that the name returns the required path for initialize 
        transactions url'''

        url_name = reverse('paystack_initialize')
        url_path = '/paystack/initialize/'
        self.assertEqual(url_name, url_path)

    def test_resolve_account_number_url(self):
        '''assert that the name returns the required path for resolve account 
        number url'''

        url_name = reverse('paystack_resolve_acct_number')
        url_path = '/paystack/resolve-account-bank/'
        self.assertEqual(url_name, url_path)

    def test_chicken_change_deposit_url(self):
        '''assert that the name returns the required path for chicken 
        change deposit url'''

        url_name = reverse('chicken_change_deposit')
        url_path = '/api/v1/chicken-change-deposit/'
        self.assertEqual(url_name, url_path)



class TransactionsUrlsResolvesToViewTest(SimpleTestCase):

    def test_list_create_transactions_resolves_to_view(self):
        '''assert that list create transactions url resolves to the list create transactions
         view class'''

        # resolves to the func.view_class

        found = resolve('/api/v1/users/me/accounts/type_of_account/transactions/')
        self.assertEquals(found.func.view_class, views.ListCreateTransactionsView)

    def test_initialize_transactions_resolves_to_view(self):
        '''assert that initialize_transactions url resolves to the initialize_transactions
         view class'''

        # resolves to the func.view_class

        found = resolve('/paystack/initialize/')
        self.assertEquals(found.func.view_class, views.InitializeTransaction)

    def test_resolve_account_number_resolves_to_view(self):
        '''assert that resolve_account_number url resolves to the resolve_account_number
         view class'''

        # resolves to the func.view_class

        found = resolve('/paystack/resolve-account-bank/')
        self.assertEquals(found.func.view_class, views.ResolveAccountNumber)

    def test_chicken_change_deposit_to_view(self):
        '''assert that chicken_change_deposit url resolves to the chicken_change_deposit
         view class'''

        # resolves to the func.view_class

        found = resolve('/api/v1/chicken-change-deposit/')
        self.assertEquals(found.func.view_class, views.ChickenChangeView)


    