from django.test import SimpleTestCase
from django.urls import reverse, resolve

from deposits import views



class FundSourceUrlsPatternsTest(SimpleTestCase):
    
    def test_add_card_url(self):
        '''assert that the name returns the required path for add_card
        fundsource url'''

        url_name = reverse('paystack_addcard')
        url_path = '/paystack/add_card'
        self.assertEqual(url_name, url_path)

    def test_fund_sources_url(self):
        '''assert that the name returns the required path for fund_sources
         url'''

        url_name = reverse('fund_sources')
        url_path = '/api/v1/users/me/fund_sources/'
        self.assertEqual(url_name, url_path)

    def test_default_fund_sources_url(self):
        '''assert that the name returns the required path for default_fund_sources
         url'''

        url_name = reverse('default_fund_source')
        url_path = '/api/v1/users/me/fund_sources/set_default/'
        self.assertEqual(url_name, url_path)



class FundSourceUrlsResolvesToViewTest(SimpleTestCase):

    def test_add_card_resolves_to_view(self):
        '''assert that add_card url resolves to the add_card fund_source
        view class'''

        # resolves to the func.view_class
        found = resolve('/paystack/add_card')
        self.assertEquals(found.func.view_class, views.PaystackAddCard)

    def test_fund_sources_resolves_to_view(self):
        '''assert that fund_sources url resolves to the fund_sources
        view class'''

        found = resolve('/api/v1/users/me/fund_sources/')
        self.assertEquals(found.func.view_class, views.RetrieveFundSourceView)

    def test_default_fund_sources_to_view(self):
        '''assert that default_fund_sources url resolves to the default_fund_sources
        view class'''

        found = resolve('/api/v1/users/me/fund_sources/set_default/')
        self.assertEquals(found.func.view_class, views.ChangeDefaultFundSource)


