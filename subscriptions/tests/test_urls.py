from django.test import SimpleTestCase
from django.urls import reverse, resolve

from subscriptions import views




class SubscriptionsUrlsPatternsTest(SimpleTestCase):
    
    def test_retrieve_update_subscriptions_url(self):
        '''assert that the name returns the required path for retrieve update 
        subscriptions url'''

        url_name = reverse('subscriptions:subscription', args=['type_of_account'])
        url_path = '/api/v1/users/me/accounts/type_of_account/subscription'
        self.assertEqual(url_name, url_path)

    def test_enable_subscriptions_url(self):
        '''assert that the name returns the required path for enable subscriptions url'''

        url_name = reverse('subscriptions:enable_subscription', args=['type_of_account'])
        url_path = '/api/v1/users/me/accounts/type_of_account/subscription/enable'
        self.assertEqual(url_name, url_path)

    def test_disable_subscriptions_url(self):
        '''assert that the name returns the required path for disable subscriptions url'''

        url_name = reverse('subscriptions:disable_subscription', args=['type_of_account'])
        url_path = '/api/v1/users/me/accounts/type_of_account/subscription/disable'
        self.assertEqual(url_name, url_path)

    def test_create_subscriptions_url(self):
        '''assert that the name returns the required path for create subscriptions url'''

        url_name = reverse('subscriptions:subscriptions', args=['type_of_account'])
        url_path = '/api/v1/users/me/accounts/type_of_account/subscriptions'
        self.assertEqual(url_name, url_path)



class SubscriptionsUrlsResolvesToViewTest(SimpleTestCase):

    def test_retrieve_update_resolves_to_view(self):
        '''assert that retrieve_update url resolves to the retrieve_update subscriptions
        view class'''

        # resolves to the func.view_class

        found = resolve('/api/v1/users/me/accounts/type_of_account/subscription')
        self.assertEquals(found.func.view_class, views.RetrieveUpdateSubscriptionView)

    def test_enable_subscriptions_resolves_to_view(self):
        '''assert that enable_subscriptions url resolves to the enable_subscriptions
        view class'''

        found = resolve('/api/v1/users/me/accounts/type_of_account/subscription/enable')
        self.assertEquals(found.func.view_class, views.EnableSubscription)


    def test_disable_subscriptions_resolves_to_view(self):
        '''assert that disable_subscriptions url resolves to the disable_subscriptions 
        view class'''

        found = resolve('/api/v1/users/me/accounts/type_of_account/subscription/disable')
        self.assertEquals(found.func.view_class, views.DisableSubscription)


    def test_create_subscriptions_resolves_to_view(self):
        '''assert that create_subscriptions url resolves to the create_subscriptions
        view class'''

        found = resolve('/api/v1/users/me/accounts/type_of_account/subscriptions')
        self.assertEquals(found.func.view_class, views.CreateSubscriptionsView)
