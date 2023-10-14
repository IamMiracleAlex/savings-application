from django.test import SimpleTestCase
from django.urls import reverse, resolve

from accounts import views




class AccountsUrlsPatternsTest(SimpleTestCase):
    
    def test_list_accounts_url(self):
        '''assert that the name returns the required path for list accounts'''

        url_name = reverse('accounts:accounts')
        url_path = '/api/v1/users/me/accounts/'
        self.assertEqual(url_name, url_path)

    def test_get_account_url(self):
        '''assert that the name returns the required path for get accounts'''

        url_name = reverse('accounts:account', args=['type_of_account'])
        url_path = '/api/v1/users/me/accounts/type_of_account'
        self.assertEqual(url_name, url_path)



class AccountUrlsResolvesToViewTest(SimpleTestCase):

    def test_list_account_resolves_to_view(self):
        '''assert that list account url resolves to the list account view class'''

        found = resolve('/api/v1/users/me/accounts/')

        # resolves to the view class
        self.assertEquals(found.func.view_class, views.ListAccountsView)

    
    def test_get_account_resolves_view(self):
        '''assert that get account url resolves to the get account view class'''

        found = resolve('/api/v1/users/me/accounts/type_of_account')
        self.assertEquals(found.func.view_class, views.GetAccountView ) 

    